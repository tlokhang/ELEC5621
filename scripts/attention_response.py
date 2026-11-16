"""Cue-to-target subsystem experiment, paired repeats, and measured-yaw animation."""
import argparse
import csv
import json
import math

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import mujoco
import numpy as np

from head_stabilization import ROOT, SCENE, simulate_case

OUT = ROOT / 'results' / 'attention_response'
CASES = ('baseline', 'feedback', 'optimized')
# Engineering acceptance criteria chosen before running this experiment.
CRITERIA = dict(acquire_tolerance_deg=3, acquire_dwell_s=0.2,
                acquire_deadline_s=1, hold_rms_deg=3, hold_peak_deg=6)


def evaluate(rows, metrics, *, cue_delay=0.5, disturbance_start=2.0):
    t = np.array([r['time_s'] for r in rows])
    e = np.abs(np.rad2deg([r['head_yaw_error_rad'] for r in rows]))
    # Cue at 0.5 s; target acquisition before trunk disturbance at 2 s.
    if len(t) < 2 or not np.all(np.diff(t) > 0):
        raise ValueError('Require increasing sample times')
    if not np.all(np.isfinite(e)):
        raise ValueError('Nonfinite errors')
    acquired = None
    for i in np.flatnonzero((t > cue_delay) & (t <= cue_delay + CRITERIA['acquire_deadline_s'])):
        end = int(np.searchsorted(t, t[i] + CRITERIA['acquire_dwell_s'] - 1e-12))
        if end < len(t) and t[end] < disturbance_start and np.all(e[i:end+1] <= CRITERIA['acquire_tolerance_deg']):
            acquired = float(t[i] - cue_delay)
            break
    hold = e[t > disturbance_start]
    if not len(hold):
        raise ValueError("No stabilization samples")
    rms, peak = float(np.sqrt(np.mean(hold**2))), float(hold.max())
    success = (acquired is not None and acquired <= CRITERIA['acquire_deadline_s']
               and rms <= CRITERIA['hold_rms_deg'] and peak <= CRITERIA['hold_peak_deg']
               and not metrics['head_yaw_limit_exceeded'])
    return dict(acquisition_s=acquired, hold_rms_deg=rms, hold_peak_deg=peak,
                success=success, yaw_limit_exceeded=metrics['head_yaw_limit_exceeded'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-animation", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    model = mujoco.MjModel.from_xml_path(str(SCENE))
    common = dict(duration=6., settle_duration=1., cue_delay=.5,
                  disturbance_delay=1.5, sample_period=.002, gaze_gain=2.)
    trials, demo = [], {}
    # Same seed gives identical task parameters to all three controllers.
    for seed in range(12):
        rng = np.random.default_rng(seed)
        target = float(rng.choice([-1, 1]) * rng.uniform(10, 20))
        amplitude, frequency = float(rng.uniform(10, 20)), float(rng.uniform(.25, .5))
        paired = {}
        for case in CASES:
            rows, metrics = simulate_case(model, case, **common,
                target_offset=math.radians(target), torso_yaw_amplitude=math.radians(amplitude),
                frequency=frequency)
            assert all(np.isfinite(v) for row in rows for k, v in row.items() if k != 'case')
            assert not any(r['cue_active'] or abs(r['head_yaw_target_rad'] - rows[0]['head_yaw_target_rad']) > 1e-12
                           for r in rows if r['time_s'] <= .5), 'Pre-cue target leaked'
            paired[case] = evaluate(rows, metrics, cue_delay=common["cue_delay"],
                disturbance_start=common["cue_delay"] + common["disturbance_delay"])
            if seed == 0:
                demo[case] = rows
        trials.append(dict(seed=seed, target_offset_deg=target, amplitude_deg=amplitude,
                           frequency_hz=frequency, results=paired))
    aggregate = {}
    for case in CASES:
        values = [trial['results'][case] for trial in trials]
        rms = [v['hold_rms_deg'] for v in values]
        aggregate[case] = dict(successes=sum(v['success'] for v in values), trials=len(values),
            mean_hold_rms_deg=float(np.mean(rms)), std_hold_rms_deg=float(np.std(rms, ddof=1)),
            max_hold_peak_deg=max(v['hold_peak_deg'] for v in values))
    result = dict(criteria=CRITERIA, configuration=common, mujoco_version=mujoco.__version__,
        scope='Yaw-only head/neck rig with prescribed mocap torso and perfect sensing; no balance validation',
        repeats='12 paired seeded draws from the same task distribution; no sensor noise',
        trials=trials, aggregate=aggregate)
    (OUT / 'summary.json').write_text(json.dumps(result, indent=2))
    with (OUT / 'demo.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(demo['baseline'][0]))
        writer.writeheader()
        for rows in demo.values():
            writer.writerows(rows)
    fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
    for case, rows in demo.items():
        ax.plot([r['time_s'] for r in rows], np.rad2deg([r['head_yaw_error_rad'] for r in rows]), label=case)
    ax.axvline(.5, color='k', ls='--', label='Target cue')
    ax.axvline(2, color='gray', ls=':', label='Torso motion begins')
    ax.set(xlabel='Time (s)', ylabel='Gaze error (deg)', title='Cue-to-target response: seed 0')
    ax.legend(); ax.grid(alpha=.2)
    fig.savefig(OUT / 'comparison.png', dpi=150); plt.close(fig)
    if args.skip_animation:
        print(json.dumps(aggregate, indent=2))
        return
    # Top-view schematic uses measured simulator angles, not a fabricated robot video.
    fig, axes = plt.subplots(1, 3, figsize=(10, 4))
    artists = []
    for ax, case in zip(axes, CASES):
        ax.set(xlim=(-1.2, 1.2), ylim=(-1.2, 1.2), aspect='equal', title=case)
        ax.grid(alpha=.2)
        artists.append([ax.plot([], [], color=c, lw=3, label=l)[0]
                        for c, l in [('gray', 'Torso'), ('tab:blue', 'Gaze'), ('tab:orange', 'Target')]])
    axes[0].legend(loc='lower left', fontsize=8)
    title = fig.suptitle('')
    def update(frame):
        index = frame * 25  # 20 fps at 2 ms physics sampling
        for case, lines in zip(CASES, artists):
            row = demo[case][index]
            for line, key in zip(lines, ('trunk_yaw_rad', 'head_yaw_world_rad', 'head_yaw_target_rad')):
                angle = row[key]
                line.set_data([0, math.cos(angle)], [0, math.sin(angle)])
        t = demo['baseline'][index]['time_s']
        title.set_text(f'{t:.2f}s | ' + ('WAIT' if t <= .5 else 'ORIENT' if t < 2 else 'STABILIZE')
                       + ' | Measured yaw schematic; supported trunk')
    animation = FuncAnimation(fig, update, frames=len(demo['baseline']) // 25, interval=50)
    animation.save(OUT / 'demo.gif', writer=PillowWriter(fps=20)); plt.close(fig)
    print(json.dumps(aggregate, indent=2))
    print(f'Saved experiment and measured-yaw animation to {OUT}')


if __name__ == '__main__':
    main()
