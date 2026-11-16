"""Reproducible parameter sweep and regression checks for the head/neck rig."""
import json
import math

import mujoco
import numpy as np

from head_stabilization import ROOT, SCENE, simulate_case


def main():
    model = mujoco.MjModel.from_xml_path(str(SCENE))
    common = dict(duration=5.0, settle_duration=1.0, cue_delay=0.5,
                  sample_period=0.01, gaze_gain=2.0)
    trials = []
    for amplitude in (10, 20, 30):
        for frequency in (0.25, 0.5, 1.0):
            results = {}
            signals = []
            for case in ("baseline", "feedback", "optimized"):
                rows, metrics = simulate_case(model, case, **common,
                    torso_yaw_amplitude=math.radians(amplitude), frequency=frequency)
                assert all(np.isfinite(float(value)) for row in rows for key, value in row.items() if key != "case")
                assert not metrics["head_yaw_limit_exceeded"]
                signals.append([row["trunk_yaw_rad"] for row in rows])
                results[case] = metrics
            np.testing.assert_allclose(signals[0], signals[1], atol=1e-12)
            np.testing.assert_allclose(signals[0], signals[2], atol=1e-12)
            assert results["optimized"]["rms_head_yaw_error_rad"] < results["feedback"]["rms_head_yaw_error_rad"]
            trials.append(dict(amplitude_deg=amplitude, frequency_hz=frequency, metrics=results))

    kwargs = dict(common, torso_yaw_amplitude=math.radians(20), frequency=0.5)
    _, dense = simulate_case(model, "optimized", **kwargs)
    kwargs["sample_period"] = 0.1
    _, sparse = simulate_case(model, "optimized", **kwargs)
    assert dense == sparse, "CSV sampling must not change metrics"
    for invalid in (dict(duration=0), dict(cue_delay=5), dict(frequency=0),
                    dict(sample_period=0), dict(gaze_gain=float("nan"))):
        try:
            simulate_case(model, "optimized", **(kwargs | invalid))
        except ValueError:
            pass
        else:
            raise AssertionError(f"Invalid parameters accepted: {invalid}")
    output = ROOT / "results" / "head_stabilization" / "verification.json"
    output.write_text(json.dumps(dict(trials=trials, sampling_invariance=True,
        invalid_inputs_rejected=True, mujoco_version=mujoco.__version__), indent=2))
    print(f"Passed nine amplitude/frequency comparisons, sampling invariance, and five invalid-input checks. Saved {output}")
    for trial in trials:
        print(trial["amplitude_deg"], trial["frequency_hz"],
              {case: round(math.degrees(values["rms_head_yaw_error_rad"]), 3)
               for case, values in trial["metrics"].items()})


if __name__ == "__main__":
    main()
