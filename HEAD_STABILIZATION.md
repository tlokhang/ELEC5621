# Microduck Head Stabilization Prototype

This project tests whether Microduck's actuated head yaw can keep its camera gaze steady while the trunk turns. It uses the official Microduck head/neck model and compares a neutral head-yaw hold with trunk-yaw compensation.

## Run

From the project root, with Python 3.12 and `uv` available:

```bash
uv sync
uv run python scripts/build_head_rig.py
uv run python scripts/head_stabilization.py
```

To change the default torso motion or output path:

```bash
uv run python scripts/head_stabilization.py \
  --duration 4 \
  --settle-duration 1 \
  --cue-delay 0.5 \
  --torso-yaw-amplitude-deg 20 \
  --frequency 0.5 \
  --output-dir results/head_stabilization/head_neck_rig
```

The script writes `trials.csv`, `summary.json`, and `comparison.png` under `results/head_stabilization/head_neck_rig/`.

## Reviewed result

The corrected 4 s run at 20° and 0.5 Hz compares three cases. Gaze-yaw RMS error is 14.13° for nominal hold, 4.56° for the original trunk-angle compensation (`feedback` in the CSV), and 1.51° for compensation plus proportional gaze-error feedback (`optimized`, gain 2). The optimized peak error is 2.85°. RMS error improves 89.3% relative to nominal hold, or 66.9% relative to the original compensation.

The controller uses `q_command = q_reference - trunk_yaw_delta / yaw_gain - gaze_gain * gaze_error / yaw_gain`, clipped to the joint limits. It retains the original actuator parameters. Gaze is perfect simulator state; noisy sensing and delay remain untested. Use `--gaze-gain` to change the feedback gain.

Kinematics are refreshed after integration before measurements are recorded. Metrics use every 2 ms physics step; `--sample-period` controls CSV/plot decimation only. Historical 67.1% figures used the earlier measurement timing and should not be compared directly with the corrected measurements.

Run `uv run python scripts/verify_head_stabilization.py` for nine deterministic amplitude/frequency cases (10°, 20°, 30° at 0.25, 0.5, 1 Hz), checks for finite states and yaw limits, identical torso inputs, CSV-sampling invariance, and invalid parameters. All passed. Optimized RMS errors range from 0.50° to 4.45° and improve on the original controller in every case. These are parameter sweeps, not statistical repetitions.

See [the plot](results/head_stabilization/head_neck_rig/comparison.png), [default metrics](results/head_stabilization/head_neck_rig/summary.json), and [sweep results](results/head_stabilization/verification.json).

## What this demonstrates

The head/neck subassembly uses the official `neck_pitch`, `head_pitch`, `head_yaw`, and `head_roll` joints, mesh assets, inertias, and position actuators. The controller holds the official camera's world-frame viewing direction by compensating for measured trunk yaw.

The trunk is a MuJoCo mocap body and its yaw trajectory is prescribed. Both controllers run against the same input. This isolates gaze stabilization; it does **not** simulate standing, walking, torso dynamics, or whole-body balance. The official STAND keyframe falls without a stand controller, even when no perturbation is applied. The initial result is one deterministic trial with perfect state information, so it does not establish statistical robustness or noisy-sensor performance.

## Model source and attribution

The source revision, model transformation, and applicable licenses are documented in [assets/microduck/SOURCE.md](assets/microduck/SOURCE.md). STL assets are CC BY-NC-SA 4.0; the copied upstream license files are included beside the model.

## Next extension

To connect this to the full course scenario, add a standing controller or trained standing policy, then run the head controller on the dynamically moving biped. The RTX 3060 is available for parallel PPO training; it was not used in this deterministic single-rig comparison. A useful next experiment is to repeat trials over torso amplitudes/frequencies, then add IMU noise and delay before comparing with a GPU-trained policy.

Mocap torso pose changes do not provide a fully dynamic base-motion model with physical angular velocity/acceleration coupling. A dynamic driven base is needed before drawing conclusions about rejection of inertial disturbances.

## Cue-to-target extension
See ATTENTION_RESPONSE.md and run `uv run python scripts/attention_response.py` for the new target-cue experiment, 12 paired trials, and measured-yaw schematic GIF. This uses the same supported head/neck rig.
