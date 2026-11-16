"""Compare fixed head-yaw hold with trunk-yaw compensation on a Microduck head/neck rig."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mujoco
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
SCENE = ROOT / "assets" / "microduck" / "head_neck_rig.xml"


def wrap_angle(angle: float) -> float:
    return (angle + math.pi) % (2.0 * math.pi) - math.pi


def quat_yaw(quat: np.ndarray) -> float:
    w, x, y, z = quat
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def camera_gaze_yaw(data: mujoco.MjData, camera_id: int) -> float:
    """Azimuth of the camera optical axis (MuJoCo camera looks along local -Z)."""
    camera_rotation = data.cam_xmat[camera_id].reshape(3, 3)
    gaze_vector = -camera_rotation[:, 2]
    return math.atan2(float(gaze_vector[1]), float(gaze_vector[0]))


def named_id(model: mujoco.MjModel, kind: mujoco.mjtObj, name: str) -> int:
    result = mujoco.mj_name2id(model, kind, name)
    if result < 0:
        raise ValueError(f"Model is missing {kind.name} named {name!r}")
    return result


def head_yaw_gain(
    model: mujoco.MjModel,
    camera_id: int,
    yaw_joint_id: int,
) -> float:
    """Estimate world-head-yaw change per radian of the head_yaw joint."""
    data = mujoco.MjData(model)
    trunk_id = named_id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk_base")
    mocap_id = int(model.body_mocapid[trunk_id])
    data.mocap_pos[mocap_id] = (0.0, 0.0, 0.12)
    data.mocap_quat[mocap_id] = (1.0, 0.0, 0.0, 0.0)
    mujoco.mj_forward(model, data)
    qpos_id = model.jnt_qposadr[yaw_joint_id]
    yaw_before = camera_gaze_yaw(data, camera_id)
    epsilon = 1.0e-3
    data.qpos[qpos_id] += epsilon
    mujoco.mj_forward(model, data)
    yaw_after = camera_gaze_yaw(data, camera_id)
    gain = wrap_angle(yaw_after - yaw_before) / epsilon
    if abs(gain) < 0.25:
        raise ValueError(f"head_yaw has unexpectedly small world-yaw gain: {gain:.4f}")
    return gain


def simulate_case(
    model: mujoco.MjModel,
    case: str,
    *,
    duration: float,
    settle_duration: float,
    cue_delay: float,
    torso_yaw_amplitude: float,
    frequency: float,
    sample_period: float,
    gaze_gain: float = 2.0,
    target_offset: float = 0.0,
    disturbance_delay: float = 0.0,
) -> tuple[list[dict[str, float | str]], dict[str, float | bool]]:
    values = (duration, settle_duration, cue_delay, torso_yaw_amplitude, frequency, sample_period, gaze_gain, target_offset, disturbance_delay)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("All trial parameters must be finite")
    if duration <= 0 or not 0 <= cue_delay < duration or settle_duration < 0:
        raise ValueError("Require duration > cue_delay >= 0 and settle_duration >= 0")
    if frequency <= 0 or sample_period <= 0 or gaze_gain < 0:
        raise ValueError("Frequency/sample period must be positive and gaze gain nonnegative")
    if duration - cue_delay < model.opt.timestep or torso_yaw_amplitude < 0:
        raise ValueError("Require an active window of at least one physics step and nonnegative amplitude")
    if disturbance_delay < 0 or cue_delay + disturbance_delay >= duration:
        raise ValueError("Disturbance must start within the trial")
    if case not in ("baseline", "feedback", "optimized"):
        raise ValueError(f"Unknown case: {case}")
    data = mujoco.MjData(model)
    trunk_id = named_id(model, mujoco.mjtObj.mjOBJ_BODY, "trunk_base")
    mocap_id = int(model.body_mocapid[trunk_id])
    if mocap_id < 0:
        raise ValueError("head_neck_rig.xml must expose trunk_base as a mocap body")
    camera_id = named_id(model, mujoco.mjtObj.mjOBJ_CAMERA, "head_camera")
    yaw_joint_id = named_id(model, mujoco.mjtObj.mjOBJ_JOINT, "head_yaw")
    yaw_qpos_id = model.jnt_qposadr[yaw_joint_id]
    yaw_actuator_id = next(
        actuator_id
        for actuator_id, (joint_id, _) in enumerate(model.actuator_trnid)
        if joint_id == yaw_joint_id
    )
    yaw_gain = head_yaw_gain(model, camera_id, yaw_joint_id)

    mujoco.mj_resetData(model, data)
    data.mocap_pos[mocap_id] = (0.0, 0.0, 0.12)
    data.mocap_quat[mocap_id] = (1.0, 0.0, 0.0, 0.0)
    mujoco.mj_forward(model, data)
    reference_ctrl = np.asarray(
        [model.qpos0[model.jnt_qposadr[joint_id]] for joint_id, _ in model.actuator_trnid],
        dtype=float,
    )
    reference_head_joint = float(data.qpos[yaw_qpos_id])

    for _ in range(round(settle_duration / model.opt.timestep)):
        data.mocap_pos[mocap_id] = (0.0, 0.0, 0.12)
        data.mocap_quat[mocap_id] = (1.0, 0.0, 0.0, 0.0)
        data.ctrl[:] = reference_ctrl
        mujoco.mj_step(model, data)

    mujoco.mj_forward(model, data)
    reference_trunk_yaw = quat_yaw(data.xquat[trunk_id])
    initial_head_yaw = camera_gaze_yaw(data, camera_id)
    target_head_yaw = initial_head_yaw
    rows: list[dict[str, float | str]] = []
    max_head_force = 0.0
    sample_stride = max(1, round(sample_period / model.opt.timestep))
    total_steps = round(duration / model.opt.timestep)

    for step in range(total_steps):
        time = step * model.opt.timestep
        cue_active = time >= cue_delay
        target_head_yaw = wrap_angle(initial_head_yaw + (target_offset if cue_active else 0.0))
        disturbance_time = time - cue_delay - disturbance_delay
        torso_yaw_command = 0.0
        if disturbance_time >= 0.0:
            torso_yaw_command = torso_yaw_amplitude * math.sin(2.0 * math.pi * frequency * disturbance_time)
        data.mocap_pos[mocap_id] = (0.0, 0.0, 0.12)
        data.mocap_quat[mocap_id] = (
            math.cos(torso_yaw_command / 2.0),
            0.0,
            0.0,
            math.sin(torso_yaw_command / 2.0),
        )
        mujoco.mj_forward(model, data)
        data.ctrl[:] = reference_ctrl
        trunk_yaw = quat_yaw(data.xquat[trunk_id])
        if case in ("feedback", "optimized"):
            body_yaw_delta = wrap_angle(trunk_yaw - reference_trunk_yaw)
            command = reference_head_joint + (target_offset if cue_active else 0.0) / yaw_gain - body_yaw_delta / yaw_gain
            if case == "optimized":
                gaze_error = wrap_angle(camera_gaze_yaw(data, camera_id) - target_head_yaw)
                command -= gaze_gain * gaze_error / yaw_gain
            lower, upper = model.jnt_range[yaw_joint_id]
            data.ctrl[yaw_actuator_id] = float(np.clip(command, lower, upper))
        elif case == "baseline":
            lower, upper = model.jnt_range[yaw_joint_id]
            data.ctrl[yaw_actuator_id] = float(np.clip(reference_head_joint + (target_offset if cue_active else 0.0) / yaw_gain, lower, upper))
        else:
            raise ValueError(f"Unknown case: {case}")

        mujoco.mj_step(model, data)
        # Refresh derived poses so gaze and qpos describe the same integrated state.
        mujoco.mj_forward(model, data)
        time = (step + 1) * model.opt.timestep

        trunk_yaw = quat_yaw(data.xquat[trunk_id])
        head_yaw = camera_gaze_yaw(data, camera_id)
        yaw_error = wrap_angle(head_yaw - target_head_yaw)
        actuator_force = float(data.actuator_force[yaw_actuator_id])
        max_head_force = max(max_head_force, abs(actuator_force))
        rows.append(
            {
                "case": case,
                "time_s": time,
                "cue_active": float(cue_active),
                "trunk_yaw_command_rad": torso_yaw_command,
                "trunk_yaw_rad": trunk_yaw,
                "head_yaw_world_rad": head_yaw,
                "head_yaw_target_rad": target_head_yaw,
                "head_yaw_error_rad": yaw_error,
                "head_yaw_command_rad": float(data.ctrl[yaw_actuator_id]),
                "head_actuator_force_nm": actuator_force,
                "head_yaw_joint_rad": float(data.qpos[yaw_qpos_id]),
            }
        )

    forces = np.asarray([float(row["head_actuator_force_nm"]) for row in rows])
    active_errors = np.asarray(
        [
            float(row["head_yaw_error_rad"])
            for row in rows
            if bool(row["cue_active"])
        ]
    )
    metrics: dict[str, float | bool] = {
        "rms_head_yaw_error_rad": float(np.sqrt(np.mean(active_errors**2))),
        "peak_head_yaw_error_rad": float(np.max(np.abs(active_errors))),
        "rms_head_actuator_force_nm": float(np.sqrt(np.mean(forces**2))),
        "max_head_actuator_force_nm": max_head_force,
        "peak_abs_head_yaw_joint_rad": float(np.max(np.abs([row["head_yaw_joint_rad"] for row in rows]))),
        "head_yaw_gain": yaw_gain,
        "head_yaw_limit_exceeded": any(not model.jnt_range[yaw_joint_id, 0] <= float(row["head_yaw_joint_rad"]) <= model.jnt_range[yaw_joint_id, 1] for row in rows),
    }
    return rows[::sample_stride], metrics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "head_stabilization" / "head_neck_rig")
    parser.add_argument("--duration", type=float, default=4.0, help="Trial duration in seconds")
    parser.add_argument("--settle-duration", type=float, default=1.0, help="Initial fixed-torso settling time")
    parser.add_argument("--cue-delay", type=float, default=0.5, help="Seconds before the disturbance cue")
    parser.add_argument("--torso-yaw-amplitude-deg", type=float, default=20.0, help="Prescribed trunk yaw amplitude")
    parser.add_argument("--frequency", type=float, default=0.5, help="Disturbance frequency in Hz")
    parser.add_argument("--sample-period", type=float, default=0.01, help="CSV sampling period in seconds")
    parser.add_argument("--gaze-gain", type=float, default=2.0, help="Dimensionless gaze error feedback gain")
    args = parser.parse_args()

    if not SCENE.exists():
        raise FileNotFoundError(f"Scene not found: {SCENE}")
    model = mujoco.MjModel.from_xml_path(str(SCENE))
    rows: list[dict[str, float | str]] = []
    metrics: dict[str, dict[str, float | bool]] = {}
    for case in ("baseline", "feedback", "optimized"):
        case_rows, case_metrics = simulate_case(
            model,
            case,
            duration=args.duration,
            settle_duration=args.settle_duration,
            cue_delay=args.cue_delay,
            torso_yaw_amplitude=math.radians(args.torso_yaw_amplitude_deg),
            frequency=args.frequency,
            sample_period=args.sample_period,
            gaze_gain=args.gaze_gain,
        )
        rows.extend(case_rows)
        metrics[case] = case_metrics

    args.output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = args.output_dir / "trials.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    baseline_rmse = float(metrics["baseline"]["rms_head_yaw_error_rad"])
    feedback_rmse = float(metrics["feedback"]["rms_head_yaw_error_rad"])
    improvement = 100.0 * (1.0 - feedback_rmse / max(baseline_rmse, 1.0e-9))
    summary = {
        "experiment": "world-frame camera gaze stabilization under prescribed torso yaw",
        "model": "Pollen Robotics Microduck head/neck subassembly with a kinematic trunk",
        "controller": "baseline, original trunk compensation, and compensation plus gaze-error feedback",
        "scope_limit": "The trunk trajectory is prescribed; this experiment does not evaluate standing or whole-body balance.",
        "configuration": {
            "timestep_s": float(model.opt.timestep),
            "duration_s": args.duration,
            "settle_duration_s": args.settle_duration,
            "cue_delay_s": args.cue_delay,
            "torso_yaw_amplitude_deg": args.torso_yaw_amplitude_deg,
            "disturbance_frequency_hz": args.frequency,
            "sample_period_s": args.sample_period,
            "gaze_feedback_gain": args.gaze_gain,
            "metric_sampling_period_s": float(model.opt.timestep),
        },
        "metrics": metrics,
        "feedback_rms_error_improvement_percent": improvement,
        "optimized_rms_error_improvement_percent": 100.0 * (1.0 - float(metrics["optimized"]["rms_head_yaw_error_rad"]) / max(baseline_rmse, 1e-9)),
    }
    summary_path = args.output_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True, constrained_layout=True)
    for case, label in (("baseline", "Nominal head-yaw hold"), ("feedback", "Trunk-yaw compensation"), ("optimized", "Compensation + gaze feedback")):
        case_rows = [row for row in rows if row["case"] == case]
        time = np.asarray([float(row["time_s"]) for row in case_rows])
        error = np.rad2deg([float(row["head_yaw_error_rad"]) for row in case_rows])
        trunk = np.rad2deg([float(row["trunk_yaw_command_rad"]) for row in case_rows])
        axes[0].plot(time, error, label=label)
        axes[1].plot(time, trunk, label=label)
    axes[0].axvline(args.cue_delay, color="0.4", linestyle="--", linewidth=1, label="Cue")
    axes[0].set_ylabel("Head yaw error (deg)")
    axes[1].axvline(args.cue_delay, color="0.4", linestyle="--", linewidth=1)
    axes[1].set_ylabel("Prescribed trunk yaw (deg)")
    axes[1].set_xlabel("Time (s)")
    for axis in axes:
        axis.grid(True, alpha=0.25)
        axis.legend(loc="best")
    plot_path = args.output_dir / "comparison.png"
    fig.savefig(plot_path, dpi=160)
    plt.close(fig)

    print(json.dumps(summary, indent=2))
    print(f"Saved: {csv_path}")
    print(f"Saved: {summary_path}")
    print(f"Saved: {plot_path}")


if __name__ == "__main__":
    main()
