# Progress Log

Use this file as the chronological record of work performed, files changed, validation results, and errors.

## Session: 2026-11-14

### Phase 1: Requirements & Discovery

- **Status:** complete
- **Started:** 2026-11-14 (Asia/Hong_Kong)
- **Actions taken:**
  - Read the project brief and the repository's Microduck simulation setup guide.
  - Confirmed the brief allows MuJoCo and feedback/rule-based control, and requires measurable goals and baseline comparison.
  - Searched local project files; no robot model or simulation source is present in the initial scan.
  - Located the requested planning skill online because it is not installed locally.
  - Confirmed Python 3.12.3, NumPy, and Matplotlib exist, but MuJoCo and `uv` do not.
  - Inspected the official upstream MJCF and found actuated neck pitch/head pitch/yaw/roll joints.
- **Files created/modified:** `task_plan.md`, `findings.md`, `progress.md`.

### Phase 2: Planning & Structure

- **Status:** complete
- **Actions taken:**
  - Confirmed WSL sees an RTX 3060 with 6 GiB VRAM and a CUDA-capable driver.
  - Chose to establish a measurable feedback-control baseline first, then attempt modest GPU PPO training if the stack fits.
  - Found system Python 3.12.3 has neither MuJoCo nor pip; `uv` is also absent.
  - Selected the official ground-contact MJCF and its STAND keyframe.
  - Defined the first experiment: compare nominal head-yaw hold with trunk-yaw feedback during repeatable torso yaw disturbance.
  - Installed standalone `uv` under `/tmp/uv-bin` and synced project-local MuJoCo 3.17.0, NumPy 2.5.4, and Matplotlib 3.11.2.
  - Copied the exact official ground-contact MJCF and all 38 referenced STL assets, with upstream licenses and source revision documented.
  - Adapted the official scene wrapper and successfully loaded it in MuJoCo (16 bodies, 21 qpos, 14 actuators, four keyframes).
- **Files created/modified:**
  - `pyproject.toml`, `uv.lock`, `.gitignore`
  - `assets/microduck/robot_groundcontact.xml`, `assets/microduck/assets/*.stl`, upstream license files, and `SOURCE.md`
  - `assets/microduck/scene_head_stabilization.xml`

### Phase 3: Implementation

- **Status:** in_progress
- **Actions taken:**
  - Wrote the paired baseline/feedback simulation script and confirmed the actual camera optical axis has unit yaw gain.
  - Corrected the initial measurement implementation, then ran the pair successfully and saved outputs.
  - Found both full-body trials fall (trunk pitch reached about 1.47 rad); the head-error comparison is not interpretable until the standing condition is addressed.
  - Ran an undisturbed 2 s STAND hold; it also falls by about 0.9 s (trunk pitch about 1.30 rad), showing STAND is a keyframe rather than a controller.
  - Narrowed the first proof of concept to the official head/neck dynamics under a kinematically prescribed torso trajectory; it will not claim full-body balance.
  - Added `scripts/build_head_rig.py` to derive a kinematically supported trunk plus original head/neck chain; the resulting rig compiled successfully (6 bodies, 4 joints/actuators, 1 mocap body).
- **Verification:** revised paired rollout completed at 20° and 0.5 Hz; feedback reduced camera-gaze RMS error 67.1% in this single deterministic trial.
- **Files created/modified:** `scripts/head_stabilization.py`, `scripts/build_head_rig.py`, `assets/microduck/head_neck_rig.xml`, `results/head_stabilization/{trials.csv,summary.json,comparison.png}`.

### Phase 4: Simulation & Verification

- **Status:** complete
- **Actions taken:**
  - Ran the paired head/neck rig trial; feedback reduced gaze error and remained well within the `head_yaw` range.
  - Kept the failed full-body STAND trials separate and documented that the head-only result is not a balance result.
- **Files created/modified:**
  - `results/head_stabilization/head_neck_rig/{trials.csv,summary.json,comparison.png}`

### Phase 5: Delivery

- **Status:** complete
- **Actions taken:**
  - Added `HEAD_STABILIZATION.md` with run steps, baseline results, source attribution, and scope limits.
  - Linked the prototype guide from `Microduck_Simulation_Setup.md`.
  - Reviewed the comparison plot; the torso input traces match and the compensation trace has visibly smaller gaze error.
- **Files created/modified:** `HEAD_STABILIZATION.md`, `Microduck_Simulation_Setup.md`, `task_plan.md`, `findings.md`, `progress.md`.

## Test Results

| Test | Input | Expected | Actual | Status |
| --- | --- | --- | --- | --- |
| Runtime discovery | Project-local Python 3.12.3 environment | Import MuJoCo and plotting dependencies | MuJoCo 3.17.0, NumPy 2.5.4, Matplotlib 3.11.2 installed | complete |
| GPU discovery | `nvidia-smi` | Identify CUDA availability | RTX 3060 6 GiB is visible in WSL | complete |
| MJCF load | Project scene wrapper | Compile official robot and assets | MuJoCo loaded 16 bodies, 21 qpos, 14 actuators, 4 keyframes | complete |
| Paired rollout | 4 s baseline and feedback trials, 0.01 N m trunk-yaw torque | Both cases start and remain upright; feedback lowers head gaze error | Both fell; head error is not interpretable | failed |
| Undisturbed pose hold | Official STAND keyframe, 2 s with keyframe actuator commands | Robot remains upright before perturbation | Falls by ~0.9 s; STAND is not self-stabilizing | failed |
| Head/neck rig load | Generated head-only MJCF | Keep official head/neck chain and support prescribed trunk motion | MuJoCo loaded 6 bodies, 4 actuated joints, 1 mocap body | complete |
| Head/neck paired trial | 20° prescribed torso yaw, 0.5 Hz, 4 s | Feedback lowers camera-gaze error without hitting `head_yaw` limits | RMS 14.1° baseline vs 4.6° feedback; peak feedback error 6.5°; peak joint yaw 19.2° | complete |
| Plot review | `comparison.png` | Confirm same torso input and lower feedback gaze error | Curves match the numerical summary | complete |

## Error Log

| Timestamp | Error | Attempt | Resolution |
| --- | --- | --- | --- |
| 2026-11-14 | Bubblewrap sandbox unavailable | 1 | Read-only project inspection used the reviewed execution route. |
| 2026-11-14 | Requested skill absent from local install | 1 | Followed the public skill instructions and template structure. |
| 2026-11-14 | `python3 -m venv` could not bootstrap pip (`ensurepip`/`python3-venv` absent) | 1 | Use standalone uv installed under `/tmp` to create a project environment. |
| 2026-11-14 | `uv venv` refused the partial environment left by failed venv creation | 1 | Inspected it (`pyvenv.cfg` only); recreate with uv `--clear`. |
| 2026-11-14 | Model copy raised `FileNotFoundError` for `assets/microduck/assets/*.stl` | 1 | Create the nested assets directory explicitly before copying. |
| 2026-11-14 | First simulation stopped because head-body Euler yaw had zero sensitivity to `head_yaw` at the STAND pose | 1 | Inspect transformed head axes and switch the measurement to a head-fixed forward vector. |
| 2026-11-14 | Corrected simulation completed but both cases fell during the trial | 1 | Check undisturbed STAND hold; if it needs an unavailable policy, isolate and clearly label the head/neck subsystem. |
| 2026-11-14 | Undisturbed STAND hold falls | 1 | Use kinematic trunk excitation for the first head/neck-only validation; later integrate a trained or designed stand controller. |

## 5-Question Reboot Check

| Question | Answer |
| --- | --- |
| Where am I? | Phase 5, delivery. |
| Where am I going? | Next iteration can add repeated trials and full-body balance control. |
| What's the goal? | Build a reproducible MuJoCo head stabilization prototype using the official Microduck head/neck model. |
| What have I learned? | See `findings.md`. |
| What have I done? | Built and ran the official head/neck rig comparison, saved metrics/plot, and documented run steps and limits. |

## Review and optimization session

- Refreshed derived kinematics after integration; metrics now use every physics step independently of CSV sampling.
- Added parameter validation and gaze-error feedback while preserving the original controller.
- Strengthened model-generation checks for upstream branch/joint changes.
- Nine deterministic comparisons, sampling invariance, and five invalid-input checks passed. Regenerated default CSV, JSON, and plot.
- Documented mocap base-motion fidelity limits. Matplotlib emits an existing Axes3D import warning from mixed system/local packages; 2D artifacts are generated successfully.


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
