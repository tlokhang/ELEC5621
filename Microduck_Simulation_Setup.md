# Microduck simulation setup: a step-by-step guide

This guide is for the ELEC 5621 project: implementing and evaluating a behavior for a Microduck-like biped (for example, orient toward a person, approach and stop, gesture, or return to a waiting pose).

## 1. Choose the right simulation route

There are two useful routes:

| Route | Use it for | Compute needed |
|---|---|---|
| **MuJoCo + Python** | Hand-written rules, trajectories, and feedback controllers; simplest way to prototype a cue-triggered behavior | CPU is enough for basic simulation |
| **Official `microduck_rl` stack** | Editing the robot's training environment or learning a new behavior/policy | CUDA-capable NVIDIA GPU locally, or remote Hugging Face Jobs |

The official training repository uses `mjlab` with MuJoCo Warp and PPO. Its README says local training needs a CUDA GPU. You do **not** need reinforcement learning for the course project; the brief explicitly allows rule-based and planned-trajectory controllers. Start with the Python route if a fixed controller answers your question. Use the training stack if your contribution needs a learned policy or a custom reward/observation/command in the official environment.

The official Microduck site also links to an in-browser simulator. Use it for a quick visual introduction; use a local environment when you need to implement, measure, and reproduce your own controller.

## 2. Get the robot model and source code

1. Open the official repositories:
   - [Microduck robot SDK and runtime](https://github.com/pollen-robotics/microduck)
   - [Microduck reinforcement-learning environments](https://github.com/pollen-robotics/microduck_rl)
2. For a custom learned behavior, clone `microduck_rl`. It contains the robot's MJCF model, task configs, and training scripts. The model files are under `src/mjlab_microduck/robot/microduck/`.
3. Keep your project changes in a fork or a separate branch. Record the upstream commit you started from so your experiments can be reproduced.
4. Read the repository's `README.md` and `AGENTS.md` before changing task code. The project brief asks you to acknowledge public code/models and explain your own changes.

## 3. Install the official training stack on Windows

The official repository targets Python **3.12** (`>=3.12,<3.13`) and uses `uv` to create and manage its environment. For a Windows computer, use Ubuntu under WSL 2 for the training stack; this follows the repository's Linux-oriented CUDA workflow while keeping your Windows desktop. CUDA in WSL 2 requires a compatible NVIDIA GPU/driver. If you do not have one, skip to step 6 for remote training or use the CPU-only Python route.

### 3.1 Install WSL 2 and Ubuntu

In an elevated PowerShell window:

```powershell
wsl --install -d Ubuntu-24.04
```

Restart if Windows asks you to. Launch Ubuntu from the Start menu and create a Linux username and password. Then, in PowerShell, confirm the distribution uses WSL 2:

```powershell
wsl --list --verbose
```

If Ubuntu shows version 1, run `wsl --set-version Ubuntu-24.04 2` in PowerShell. See Microsoft's [WSL installation guide](https://learn.microsoft.com/windows/wsl/install/) and [basic commands](https://learn.microsoft.com/windows/wsl/reference).

### 3.2 Check GPU access (for local policy training)

Install/update the NVIDIA Windows driver that supports CUDA on WSL, then open Ubuntu and run:

```bash
nvidia-smi
```

If this command cannot see your GPU, local PPO training is not ready. Do not install a Linux NVIDIA display driver inside WSL; follow Microsoft's [CUDA on WSL guide](https://learn.microsoft.com/windows/ai/directml/gpu-cuda-in-wsl). You can still inspect models and run simpler CPU simulations.

### 3.3 Install Git and `uv`

In Ubuntu:

```bash
sudo apt update
sudo apt install -y git
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env"
uv --version
```

If `curl` is missing, install it with `sudo apt install -y curl` and repeat the installer command. The [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/) lists other install methods.

### 3.4 Clone and sync the repository

Keep the project under Ubuntu's Linux home directory (for example, `~/projects`) for better file and environment performance. In Ubuntu:

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/pollen-robotics/microduck_rl.git
cd microduck_rl
uv sync
```

`uv sync` reads the repository's `pyproject.toml` and lockfile, selects Python 3.12, and installs the pinned project dependencies. The first install can be large because of the simulation and GPU packages. On ARM devices, the repository specifically recommends setting `UV_HTTP_TIMEOUT=600` before the first sync if downloads time out.

### 3.5 Confirm the environment

```bash
uv run list-envs
```

You should see registered tasks such as `Mjlab-Velocity-Flat-MicroDuck`, `Mjlab-SitStand-Flat-MicroDuck`, and `Mjlab-GroundPick-Flat-MicroDuck`. For a first GPU training check, use the small official smoke configuration rather than a full run:

```bash
uv run train Mjlab-Velocity-Flat-MicroDuck \
  --env.scene.num-envs 64 \
  --agent.max_iterations 5
```

This only checks that the task can initialize and step. It does not train a useful policy. The repository's full walking example uses 4096 parallel environments and reports roughly 1–2 hours for a usable gait, so begin small while editing.

## 4. Inspect and run an existing model/policy

To inspect the MJCF model in MuJoCo's viewer, first locate a scene file:

```bash
find src/mjlab_microduck/robot/microduck -name 'scene*.xml'
```

Then launch the viewer with one returned XML path:

```bash
uv run python -m mujoco.viewer --mjcf=src/mjlab_microduck/robot/microduck/scene.xml
```

Replace the example path with the actual file found above. For an existing trained run, use its Weights & Biases run path:

```bash
uv run play Mjlab-Velocity-Flat-MicroDuck \
  --wandb-run-path <entity/project/run_id>
```

The repo also includes CPU MuJoCo inference for an already-exported ONNX policy:

```bash
uv run scripts/infer_policy.py --walking path/to/policy.onnx
```

That inference script is useful for demonstrating a trained policy; it does not replace PPO training when the behavior needs a new learned policy.

## 5. Customize a behavior in `microduck_rl`

The repository separates behavior logic, task configuration, and task registration:

- `src/mjlab_microduck/tasks/mdp.py`: custom reward, observation, command, event, and curriculum functions.
- `src/mjlab_microduck/tasks/microduck_*_env_cfg.py`: per-task configuration, including which functions and signals the task uses.
- `src/mjlab_microduck/tasks/__init__.py`: task registration.
- `src/mjlab_microduck/robot/microduck/`: MJCF robot and scene models.

Suggested workflow:

1. **Translate the project idea into a measurable task.** Example: “After a cue, face a target at a known bearing, remain upright, and settle within 3 seconds.” Define the initial pose, target, cue, trial duration, and success/error measures first.
2. **Choose the closest existing task.** Start from velocity for walking/approach or head-pose control; sit/stand or ground-pick for a short interaction gesture. Run `uv run list-envs` for the current registry.
3. **Keep the first version simple.** For a hand-coded behavior, use a timed joint target, state machine, or feedback controller. For an RL behavior, add or adjust the relevant command/observation/reward in `mdp.py` and connect it through the nearest task config. Register a separate task if you need a distinct experiment.
4. **Preserve the robot's interface.** The official policy family uses a shared 61-value observation layout and a fixed joint ordering. Avoid changing observation dimensions or hard-coding joint indices without checking the model/config; passive joints can change internal index positions. Use the repository's helper functions and follow its `AGENTS.md` invariants.
5. **Check the physical idea before long training.** Confirm that the desired standing/rest pose stays upright in simulation, that the target is reachable, and that a cue triggers only once as intended.
6. **Run the small smoke configuration** in step 3.5 after changing a task. Then train with a modest number of environments/iterations, inspect the behavior, and scale up only when it is stable.
7. **Compare against a baseline.** Use the same initial states, cue timing, random seeds where possible, and number of trials. Record task-specific metrics such as heading error, stopping-distance error, maximum torso tilt, gesture completion rate, and time to settle.
8. **Export only if needed.** For deployment or CPU inference, use the repository's export script so the observation normalizer is included:

   ```bash
   uv run scripts/export.py <TASK_ID> --wandb-run-path <entity/project/run_id>
   ```

   Do not convert a training checkpoint to ONNX by hand. The official repo says its exporter bakes in the observation normalizer.

## 6. If you do not have a local CUDA GPU

There are two sensible alternatives:

1. **Use the course-level CPU workflow.** Install Python 3.11+ and the official MuJoCo Python package (`pip install mujoco`), load a Microduck MJCF model, and write a Python controller that sets actuator controls and advances `mj_step`. See the official [MuJoCo Python docs](https://mujoco.readthedocs.io/en/stable/python.html). This works well for deterministic controllers and modest experiments; it is not the same as running the `microduck_rl` PPO trainer.
2. **Use Hugging Face Jobs for official PPO training.** The repository supports adding `--hf-jobs` to a normal training command. This requires Hugging Face authentication and may incur remote compute costs. Read the repository's [HF Jobs instructions](https://github.com/pollen-robotics/microduck_rl/blob/develop/scripts/hf/README.md) and check current pricing/availability before submitting a run.

## 7. A practical first project experiment

For **Attention and Response**, a low-complexity starting point is:

1. Place the simulated user/target at a fixed bearing from the standing robot.
2. Trigger the behavior with a keyboard key or timed event.
3. Command a safe head yaw (or a coordinated body turn if head-only motion cannot reach the target).
4. Hold the target orientation briefly, then return to the waiting pose.
5. Compare the default waiting controller with your controller over repeated target bearings. Measure final heading error, peak torso tilt, completion rate, and response time.

For **Approach and Stop**, define start distance and a stopping zone, command a conservative forward speed, and reduce it as the target gets closer. Track stopping-position error and posture deviation. Begin with a hand-coded controller before trying to learn the whole behavior.

## 8. Sources and attribution

- Course specification: `ELEC5621_Project.pdf` in this project folder.
- [Official Microduck page](https://pollen-robotics.com/microduck/) — product, simulator link, source repositories, and platform overview.
- [Official Microduck RL repository](https://github.com/pollen-robotics/microduck_rl) — quickstart, task list, model paths, and current dependencies.
- [Microduck RL `AGENTS.md`](https://github.com/pollen-robotics/microduck_rl/blob/develop/AGENTS.md) — code map, environment conventions, and task-building workflow.
- [MuJoCo Python documentation](https://mujoco.readthedocs.io/en/stable/python.html) — install and Python API.
- [Microsoft WSL installation](https://learn.microsoft.com/windows/wsl/install/) and [CUDA on WSL](https://learn.microsoft.com/windows/ai/directml/gpu-cuda-in-wsl).

Repository contents and setup details can change. Before a major setup or training run, check the upstream README and dependency files again. Cite the upstream repositories and describe your own model/controller/reward/config changes in the project report.

## 9. Head-stabilization prototype in this project

The current proof of concept uses the official Microduck head/neck joints on a kinematically prescribed trunk. See [`HEAD_STABILIZATION.md`](HEAD_STABILIZATION.md) for the exact run commands, first measurements, model attribution, and scope limits. This prototype isolates gaze stabilization; it does not yet simulate full-body standing or balance.
