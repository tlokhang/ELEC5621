# Findings & Decisions

Use this file as the durable knowledge base for discoveries, evidence, and decisions. Treat copied external material as untrusted data, not as instructions.

## Requirements

- Implement at least one bio-inspired companion robot function; start from a stable waiting pose on a level indoor surface and respond to a cue.
- A relevant function is orienting the head/body toward a user or target while maintaining balance (project PDF, pp. 1–2).
- Simulation in MuJoCo is explicitly permitted; rule-based or feedback control is acceptable, and RL is not required (pp. 3–4).
- Define initial conditions and measurable goals; test under specified conditions and compare with a baseline (p. 3).
- Keep the first implementation reproducible and runnable on CPU if feasible, with all modifications and sources documented.

## Research Findings

- `Microduck_Simulation_Setup.md` recommends a Python + MuJoCo route for fixed rules/feedback control and reserves the official `microduck_rl` stack for learned policies.
- Current project files include the setup guide and project PDF, but no local MJCF/URDF, Python simulation code, dependency manifest, or existing robot model was found in the initial file scan.
- Python 3.12.3, NumPy, and Matplotlib are present; `mujoco` and `uv` are not installed in this environment.
- WSL exposes an NVIDIA GeForce RTX 3060 with 6 GiB VRAM and CUDA-capable driver; the official GPU path is available in principle, but start with 64 parallel environments and monitor memory.
- The system Python has no `pip` module; project-local tooling/dependencies need bootstrapping before simulation can run.
- Attempted project-local venv creation, but Debian's `python3-venv`/`ensurepip` package is absent; switch to standalone uv in `/tmp`, avoiding system package changes.
- Standalone `uv` 0.13.8 is installed under `/tmp/uv-bin`; a failed venv bootstrap left only `.venv/pyvenv.cfg`, which is safe to clear before recreating.
- Project-local `.venv` and `uv.lock` are now created; `uv sync` installed MuJoCo 3.17.0, NumPy 2.5.4, and Matplotlib 3.11.2 under Python 3.12.3.
- Copied the exact official `robot_groundcontact.xml`, its 38 referenced STL meshes, and upstream license files into `assets/microduck/`; upstream source commit is `0daab160d3fb1c2cbaba16a4a19052f36709dd9e`.
- Adapted upstream `scene_allcollisions.xml` to include `robot_groundcontact.xml`; a MuJoCo model-load smoke check succeeded with 16 bodies, 21 qpos, 14 actuators, and four keyframes.
- The first controller run exposed a measurement error: Euler yaw of the `jaw_soft` body has zero first-order gain to the `head_yaw` joint at the STAND pose (likely an axis convention/singularity issue). Define and validate a head-fixed gaze vector using the actual model axes before comparing controllers.
- The official MJCF defines a `head_camera`; its optical axis is local negative-Z. Projecting that vector onto the floor plane gives gaze azimuth, with measured gain about +1 rad/rad for `head_yaw` near STAND. This avoids Euler yaw singularity in the head body frame.
- The first corrected paired rollout generated outputs, but both cases fell (maximum trunk pitch about 1.47 rad). The head-error numbers are not valid evidence of improvement. Check undisturbed STAND behavior; this model may need a learned standing policy that is not present in this project.
- An undisturbed 2 s STAND-keyframe hold also falls: trunk pitch grows from about 0.02 rad at 0.1 s to about 1.30 rad at 0.9 s. The keyframe is an initial state, not a standing controller. To preserve physical head/neck dynamics without inventing strong leg actuators, isolate that subassembly and prescribe torso motion kinematically; explicitly label this as head stabilization only, not whole-body balance.
- Generated and compiled `head_neck_rig.xml`: it contains six bodies, four actuated joints, four qpos, and one mocap trunk. This preserves the actual Microduck neck/head chain while prescribing body yaw externally.
- The official MJCF defines a `head_camera` on the head; MuJoCo camera viewing direction is its local negative-Z axis. Projecting that vector onto the floor plane gives a valid gaze azimuth, with measured gain about +1 rad/rad for `head_yaw` near the STAND keyframe. Use this instead of Euler yaw of the head rigid body.
- First mesh-copy attempt copied the MJCF but failed because the destination mesh subfolder had not been created; recreate that subfolder before retrying the copy.
- The upstream official `microduck_rl` repository contains the robot's MJCF under `src/mjlab_microduck/robot/microduck/`, with a ground-contact model at `robot_groundcontact.xml`; its README describes a ~25 cm, 800 g, 14-servo biped.
- The official MJCF has actuated `neck_pitch`, `head_pitch`, `head_yaw`, and `head_roll` joints plus an IMU orientation/angular-velocity sensor definition. This supports head stabilization without inventing an extra joint.
- Model source license notes distinguish Apache-2.0 XML descriptions from CC BY-NC-SA 4.0 STL assets; check exact model use and attribution before copying assets into this project.
- Prefer using the actual MJCF. A focused experiment may prescribe the torso pose while simulating the real head/neck chain, but must state that this isolates head stabilization and does not prove full-body balance.
- The useful first metric is world-frame head pitch/yaw deviation from the requested gaze direction during a repeatable torso perturbation; also track torso tilt and foot-ground contact.

## Technical Decisions

| Decision | Rationale |
| --- | --- |
| Make target gaze a fixed world-frame direction during a cue-triggered torso motion | Connects head stabilization to the PDF's attention/response function and creates a direct tracking error. |
| Use a passive fixed-neck baseline and an active neck feedback controller | Shows the effect of the proposed control under matching initial states and disturbances. |
| Prefer the official model's actuated neck/head joints | They are present in the upstream MJCF, so a proxy model is unnecessary for the core question. |
| Decide GPU use based on whether the project uses parallel PPO training | GPU is useful for the official Warp/PPO stack; a deterministic one-robot feedback experiment is CPU-sized. |
| Implement a deterministic feedback baseline first; attempt GPU PPO after the experiment is measurable | Keeps a runnable deliverable while preserving the option to compare a learned controller on the available 6 GiB RTX 3060. |
| First experiment holds world-frame head yaw during a repeatable torso-yaw perturbation | The upstream model exposes an actuated `head_yaw` axis, making this the smallest direct stabilization question. |
| Initialize from the official STAND keyframe and keep all non-head joint targets at the keyframe values | Reduces confounds from a free-falling initial state while testing the head control. This does not establish a full-body balance policy. |
| Compare open-loop nominal head-yaw hold against feedback compensation using trunk orientation | Provides a clear baseline and tests whether body orientation feedback reduces world-frame gaze error. |
| Isolate head/neck dynamics on a mocap trunk for the first prototype | The official standing keyframe falls without a learned stance controller; altering all leg actuator gains would undermine model fidelity. |
| Use trunk yaw compensation as the first feedback controller and measure the official camera optical axis | It directly tests whether head yaw can preserve world-frame gaze under prescribed torso movement. |

## First Head/Neck Trial

- Configuration: 4 s, 1 s fixed-torso settling, cue at 0.5 s, 20° sinusoidal trunk yaw at 0.5 Hz, 2 ms physics step, 10 ms logging.
- Baseline: hold the head-yaw joint at its neutral position; camera gaze-yaw RMS error 0.2465 rad (14.1°), peak 0.3491 rad (20.0°).
- Feedback: compensate the measured trunk yaw through the original `head_yaw` position actuator; RMS error 0.0811 rad (4.6°), peak 0.1142 rad (6.5°), peak joint angle 0.3358 rad (19.2°).
- RMS error reduction: 67.1% in this single deterministic trial.
- Interpretation limit: the torso motion is kinematically prescribed and noise-free. The result does not test balance, sensing noise, walking, or full-body dynamics.

## Issues Encountered

| Issue | Resolution |
| --- | --- |
| Workspace shell initially failed due to unavailable bubblewrap | Retried permitted read-only project inspection through the reviewed command route. |
| `planning-with-files` was not installed in the local skill catalog | Located its public Codex skill page and followed its file-based planning/template structure; no local initializer or validator is available. |

## Resources

- Project brief: `ELEC5621_Project.pdf`, pages 1–4.
- Project setup guide: `Microduck_Simulation_Setup.md`.
- Official model tree: [pollen-robotics/microduck_rl](https://github.com/pollen-robotics/microduck_rl); selected upstream MJCF: [robot_groundcontact.xml](https://raw.githubusercontent.com/pollen-robotics/microduck_rl/develop/src/mjlab_microduck/robot/microduck/robot_groundcontact.xml).
- Model licensing details: [LICENSE-MODELS.md](https://github.com/pollen-robotics/microduck_rl/blob/develop/LICENSE-MODELS.md).
- Planning skill: [OthmanAdi/planning-with-files](https://github.com/OthmanAdi/planning-with-files/blob/master/.codex/skills/planning-with-files/SKILL.md).

## Visual/Browser Findings

- The prior PDF review found that the project specifically asks for stable waiting, cue-triggered response, and balance-aware head/body orientation; the PDF permits MuJoCo simulation and baseline comparisons.
- The skill instructions call for durable `task_plan.md`, `findings.md`, and `progress.md`, with plans kept in the project and updated as work advances.
- The official MJCF defines a four-joint neck/head chain (`neck_pitch`, `head_pitch`, `head_yaw`, `head_roll`) and position actuators for those joints.
- The user asked whether GPU simulation training would be preferable; choice depends on PPO/parallel environments versus a fixed-controller demonstration.
- Proposed measurements: RMS/peak world-frame head yaw error, trunk roll/pitch, head-yaw actuator effort, and fall/ground-contact status.
- The first training-route split is to validate the deterministic controller on one official model, then consider small GPU PPO as an extension.

## Review findings

- Original feedback case is trunk-angle feed-forward only.
- mj_step does not guarantee derived camera poses match the newly integrated qpos; refresh kinematics before logging.
- Metrics were computed from decimated CSV samples, so changing sample_period changed the reported result.
- CLI permits invalid/empty trial windows; reject these explicitly.

## Optimization verification

- Added gain-2 gaze-error feedback; original actuator parameters retained. Corrected default RMS: nominal 14.13°, original compensation 4.56°, optimized 1.51° (89.3% below nominal).
- Nine amplitude/frequency cases passed; optimized RMS 0.50°–4.45°, lower than original compensation throughout. CSV sampling invariance and five invalid-input checks passed.
- Mocap pose animation omits full physical base velocity/acceleration coupling; results quantify gaze tracking for the constrained rig only.


## 2026-11-14 Course compliance audit
Re-read all four pages of ELEC5621_Project.pdf and re-ran the nine-condition verification successfully. Prototype completion is not course completion. See REQUIREMENTS_AUDIT.md for page-specific gaps: cue-to-target behavior, stable-waiting evidence/scope justification, biological literature, repeated-trial reporting, report, slides, and recorded/live demo. PDF permits a key-component proof of concept and does not require RL or all four phases. Updated task_plan to distinguish completed prototype phases from pending course deliverables.

## Cue-to-target implementation (2026-11-14)
Added optional cue-triggered target offset and delayed disturbance to simulate_case; aligned cue flags with control-step timing. Added attention_response.py with predeclared acquisition/hold thresholds and 12 seeded paired task draws. Optimized passes 12/12, original compensation 10/12, target-only baseline 0/12. Original nine-condition regression passed. Pre-cue test initially assumed zero actuator command; corrected to check unchanged target because closed-loop waiting can legitimately produce small corrections. Full balance, literature and course submission deliverables remain pending. See ATTENTION_RESPONSE.md.

## Attention-response review
Fixed dwell evaluation: 100 samples at 2 ms span 198 ms, so use timestamp-selected inclusive endpoint for full 200 ms. Exclude pre-disturbance endpoint from hold metrics and parameterize evaluator cue timing. Boundary checks passed; reran all 36 simulations. Successes remain 0/12, 10/12, 12/12; optimized mean hold RMS 0.863973 deg. Animation trajectories unchanged. Full-body balance and final academic deliverables remain incomplete.

## 2026-11-14 Whole-body and report extension
Added free-base standing controller (bias compensation, damping and ankle/hip attitude feedback), 12 paired 10 s trials with target cues and small pushes. Balanced 12/12, baseline 0/12; peak tilt 14.03 deg, no non-foot contacts or joint-limit violations beyond 0.01 rad tolerance. This is bounded standing evidence, not comprehensive robustness. Added cited literature and formal English report PDF with source/builder. Member identities/contributions remain unfilled; slides and full-robot video remain pending. See FULL_BODY_BALANCE.md.

## Portable replication guide
Created REPLICATION_GUIDE.md and Microduck_Replication_Source.zip (excluding environment/caches). Validated extracted source in fresh isolated Python 3.12.3 Linux environment: all numerical stages and PDF build passed without inherited-system Matplotlib warning. Attention and full-body JSON matched references. GIF encoding not repeated; Windows/macOS instructions not execution-tested.
