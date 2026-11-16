# Reproduce the Microduck gaze and balance project: beginner guide

This guide reproduces the implemented simulation project on another computer. It covers setup, each experiment, output interpretation, the PDF report, and common problems. The original runs used Python 3.12.3 and MuJoCo 3.17.0 in Linux/WSL. Other platforms have not been tested here; the commands below provide a portable setup path, not a claim of identical results on every machine.

## 1. What you will reproduce

The project has three related experiments:

1. **Supported head stabilization:** the trunk is prescribed to rotate while the head tries to keep looking in one world direction. This isolates head control.
2. **Attention and response:** a cue changes the desired direction, the head turns, then the trunk starts rotating. Twelve paired tasks compare three controllers.
3. **Whole-body standing:** the complete robot has a free base and contacts the floor. A controller attempts to stand while the head turns, followed by a small push. Twelve paired tasks compare standing controllers.

You also regenerate a formal English PDF report from the saved source and results. The project currently creates plots and a top-view schematic GIF, not a rendered three-dimensional whole-robot video. There is no RL training step. GPU training discussed earlier was a possible extension, not an implemented part of this project.

## 2. Computer and software requirements

A practical starting point is a modern laptop/desktop, 8 GB RAM and roughly 2 GB free disk space for Python, packages, caches and project files. These are planning estimates, not measured minimum requirements. A dedicated GPU is unnecessary for the provided numerical experiments and Matplotlib plots/GIF.

You need an Internet connection for initial Python/package downloads, a terminal, a browser/PDF viewer, and a text editor. VS Code is optional. Python 3.12 is required by this project's configuration. `uv` manages Python, the environment, and dependencies. You do not need Anaconda, a separately installed MuJoCo engine, CUDA or PyTorch.

Three names you will see:

- `pyproject.toml`: declares required Python/packages and the optional report packages.
- `uv.lock`: records resolved package versions. Keep it unchanged for reproduction.
- `.venv`: the local Python environment. Create it anew on the destination computer; do not copy one from another computer.

Official documentation: [uv installation](https://docs.astral.sh/uv/getting-started/installation/), [uv project workflow](https://docs.astral.sh/uv/guides/projects/), [MuJoCo Python installation](https://mujoco.readthedocs.io/en/stable/python.html). The MuJoCo Python package includes the engine; this project intentionally pins the 3.x series.

## 3. Transfer the project files

Use the supplied `Microduck_Replication_Source.zip`, or copy the project folder. Extract it into a normal local folder, not inside the ZIP viewer. Avoid a cloud-synced folder for the first run.

Suggested locations:

- Windows: `C:\Projects\MicroduckProject`
- macOS/Linux: `~/Projects/MicroduckProject`

The source archive extracts files directly into your chosen folder. It includes model assets, code, report source, lockfile, guides and reference outputs. It omits `.venv`, Python caches and Git internals. Reference outputs let you compare your new results but are not evidence that you have run the scripts yourself.

**Do not obtain only the upstream Microduck repository.** It supplies the robot, but not this project's controllers, tests, report builder or experiment scripts. Our local source archive is needed to reproduce the entire implementation.

Check that your extracted folder contains:

```text
MicroduckProject/
  pyproject.toml
  uv.lock
  ELEC5621_Project.pdf
  scripts/
    build_head_rig.py
    head_stabilization.py
    verify_head_stabilization.py
    attention_response.py
    full_body_balance.py
    build_report.py
  assets/microduck/
    robot_groundcontact.xml
    scene_head_stabilization.xml
    assets/                    <- 38 STL mesh files
    SOURCE.md
    LICENSE
    LICENSE-MODELS.md
  report/
    report.md
  results/                     <- supplied reference outputs; overwritten when rerun
```

Keep all model paths and filenames intact. The scripts locate the project relative to their own files, so the old `/mnt/c/...` path is not required. Windows and Linux paths are different: `/mnt/c/...` is a WSL path, not a Windows PowerShell path.

## 4. Install uv: choose your operating system

Only use the subsection for your operating system. Run commands one line at a time and wait for each to finish. Code blocks contain commands; do not type the surrounding backticks.

### Windows: PowerShell

Open PowerShell from the Start menu. Install uv using the official installer:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Close and reopen PowerShell so it sees the updated PATH. Then:

```powershell
uv --version
cd C:\Projects\MicroduckProject
Get-ChildItem
```

If your folder is elsewhere, replace the `cd` path. Quote a path containing spaces: `cd "C:\Users\YourName\My Projects\MicroduckProject"`.

You can use native Windows for these experiments. WSL is optional. If you choose WSL, use the Linux instructions inside the WSL terminal, install a separate Linux uv there, and use Linux paths. Do not reuse a Windows `.venv` inside WSL or vice versa.

### macOS: Terminal

Open Terminal and run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen Terminal, then:

```bash
uv --version
cd ~/Projects/MicroduckProject
ls
```

### Linux or WSL: terminal

Run:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Close and reopen the terminal, then:

```bash
uv --version
cd ~/Projects/MicroduckProject
ls
```

If `curl` is unavailable on Ubuntu/Debian, install it using your system package manager (`sudo apt update`, then `sudo apt install curl`). You normally do not need administrator privileges for uv itself.

## 5. Install Python and create a clean project environment

From the project folder, the following commands work in all three terminals:

```text
uv python install 3.12
uv sync --locked --extra report --python 3.12
```

Wait until downloads and installation finish. `--locked` prevents silent changes to the dependency resolution. `--extra report` installs the PDF generation/checking tools as well as simulation packages. Python patch versions may differ from the original 3.12.3; record your version when comparing results.

Use `uv run --locked --extra report` in subsequent commands so report packages remain selected. You do not need to activate `.venv` manually. Avoid plain `python`, which might invoke a different environment.

Verify the installation:

```text
uv run --locked --extra report python --version
uv run --locked --extra report python -c "import mujoco,numpy,matplotlib,reportlab,pypdf; print('MuJoCo',mujoco.__version__); print('NumPy',numpy.__version__); print('All imports succeeded')"
```

Expected: Python 3.12.x, MuJoCo 3.17.0 with the supplied lockfile, and successful imports. If you see a traceback, resolve it before proceeding.

You do not need to run the terminal as administrator or install packages globally. Do not copy the original environment, which inherited system packages and produced an avoidable Matplotlib warning.

## 6. Build the head/neck model

```text
uv run --locked --extra report python scripts/build_head_rig.py
```

Expected: a message saying it wrote `assets/microduck/head_neck_rig.xml`, retained four head/neck joints, and removed two leg branches.

This script derives the smaller experiment model from the preserved official full-body XML. It does not remove legs from the original model. The head model deliberately uses a supported/prescribed trunk; the whole-body experiment uses the original free-base model separately.

## 7. Run the basic stabilization experiment

```text
uv run --locked --extra report python scripts/head_stabilization.py
```

The program runs three cases, prints JSON statistics, and saves:

```text
results/head_stabilization/head_neck_rig/trials.csv
results/head_stabilization/head_neck_rig/summary.json
results/head_stabilization/head_neck_rig/comparison.png
```

Open `comparison.png` in your file browser. The top graph shows gaze error; the bottom shows the prescribed trunk rotation. Error nearer zero means better gaze stabilization.

Controller names in the data:

- `baseline`: hold the original head-joint position.
- `feedback`: historical name for trunk-angle compensation.
- `optimized`: compensation plus proportional gaze-error feedback.

For the default 20-degree, 0.5 Hz torso movement, approximate RMS errors are 14.13, 4.56 and 1.51 degrees respectively. Compare rounded values, not byte-for-byte JSON equality across operating systems.

**Important:** files directly inside `results/head_stabilization/` such as its old `summary.json` and `comparison.png` are preserved historical failed full-body outputs. They are not the current supported-head experiment. Use the nested `head_neck_rig/` outputs above, `verification.json` for the sweep, and `results/full_body_balance/` for the new standing experiment.

## 8. Run the nine-condition verification

```text
uv run --locked --extra report python scripts/verify_head_stabilization.py
```

This evaluates amplitudes 10, 20, 30 degrees and frequencies 0.25, 0.5, 1 Hz for each controller. It also checks finite logged values, yaw limits, identical prescribed torso inputs, CSV-sampling invariance, and rejection of five invalid input cases.

Expected terminal message starts with `Passed nine amplitude/frequency comparisons...`. Output:

```text
results/head_stabilization/verification.json
```

A failed assertion is a test failure, not a successful result. Keep the full traceback and your environment versions to investigate. The sweep is a subsystem verification; it does not establish whole-body balance.

## 9. Run cue-triggered attention and response

```text
uv run --locked --extra report python scripts/attention_response.py
```

The sequence is: settle the model; trial begins waiting; cue at 0.5 s changes the desired gaze; trunk motion starts at 2 s; trial finishes at 6 s. Twelve seeded tasks are run with the same conditions for all three controllers.

Outputs:

```text
results/attention_response/summary.json
results/attention_response/demo.csv
results/attention_response/comparison.png
results/attention_response/demo.gif
```

The GIF shows measured yaw angles as lines: grey torso, blue gaze, orange target. It is a top-view schematic, not a rendered robot. It may take longer to encode than the simulations take to run. A quiet terminal while encoding is not by itself a failure.

Expected aggregate results:

| Method | Passing tasks | Mean hold RMS | Sample standard deviation |
|---|---:|---:|---:|
| Target-only baseline | 0/12 | 10.967 degrees | 1.909 degrees |
| Trunk compensation | 10/12 | 2.603 degrees | 0.507 degrees |
| Added gaze feedback | 12/12 | 0.864 degrees | 0.166 degrees |

Each trial must acquire within 1 s of the cue and stay within 3 degrees for a complete 0.2 s. During the hold phase RMS must be at most 3 degrees and peak at most 6 degrees, with no yaw-limit exceedance.

For a faster repeat without GIF generation:

```text
uv run --locked --extra report python scripts/attention_response.py --skip-animation
```

This updates statistics, CSV and PNG but leaves any previous GIF in place. It is useful for checks; if you change the dynamics/target settings, regenerate the GIF before presenting it so it matches your new data.

## 10. Run full-body standing and head response

```text
uv run --locked --extra report python scripts/full_body_balance.py
```

This uses the actual full-body free-base robot and floor contact, not the supported head rig. It runs twelve baseline and twelve controlled trials. Each successful trial simulates ten seconds. Computation time depends on your computer and is not necessarily equal to simulated time.

For each trial: start at STAND; cue the head at 2 s; apply a small horizontal push at 5 s for 0.1 s. The terminal prints method, seed, success, and maximum tilt. `baseline ... False` is expected: the original position-hold baseline loses stability.

Outputs:

```text
results/full_body_balance/summary.json
results/full_body_balance/baseline.csv
results/full_body_balance/balanced.csv
results/full_body_balance/comparison.png
```

The CSV files are seed 0 trajectories only. The JSON stores all twelve per-method trial summaries. In the plot, the early-ending baseline trace is intentional: it terminates when a fall condition occurs.

Reference results:

- Baseline: 0/12 passing trials; it fails before the head cue, so those repeated traces are identical.
- Controlled standing: 12/12 passing ten-second trials.
- Largest controlled roll/pitch magnitude: about 14.03 degrees.
- Minimum controlled base height across trials: about 111.09 mm.
- Mean controlled gaze RMS after 3 s: about 0.127 degrees.
- No non-foot ground contacts or joint-limit violations beyond the declared 0.01 rad tolerance.

Standing passes only if base height stays at least 75 mm, roll/pitch remain within 20 degrees, and the contact/limit checks pass. These are broad finite-test criteria. The 14-degree peak means this is not precise posture regulation. The experiment does not establish walking, large-push recovery, indefinite stability, sustained double support or real-hardware performance.

The whole-body comparison changes both standing and head control. Use it to evaluate the combined extension; it does not isolate the independent contribution of each controller component. The supported-head experiments provide the cleaner gaze-controller comparison.

## 11. Regenerate and check the report

Run this after both attention and whole-body results exist:

```text
uv run --locked --extra report python scripts/build_report.py
```

Expected:

```text
.../report/ELEC5621_Report.pdf: 7 pages
```

Open `report/ELEC5621_Report.pdf` in a PDF viewer and inspect every page. The builder enforces the ten-page upper bound. You can independently print its page count:

```text
uv run --locked --extra report python -c "from pypdf import PdfReader; print(len(PdfReader('report/ELEC5621_Report.pdf').pages))"
```

Edit `report/report.md` to change the written report, then rebuild. Fill in the actual group names and contribution percentages. Read the references and check whether your interpretation matches the evidence.

**The report is only partly data-driven.** The final whole-body results table reads the current JSON automatically, and included images use the current files. Much of the prose, including the attention results, is written text. If you change experiment parameters, update all numerical statements, conditions, conclusions and figure explanations yourself before rebuilding. A successful PDF build does not certify scientific consistency.

Report references include avian reflex research, Kajita's ZMP preview-control paper, MuJoCo documentation and the pinned upstream robot source. The avian studies reviewed here concern pigeons; do not describe them as direct chicken experiments. Their indexed abstracts were reviewed; read full papers yourself before adding claims beyond those summaries.

## 12. Understand the files and measurements

| File or concept | Meaning |
|---|---|
| MJCF/XML | Robot bodies, joints, contacts, actuators and simulation settings |
| STL | Robot mesh geometry; retain the relative asset paths |
| CSV | A table of recorded signals; open with a spreadsheet or Python |
| JSON | Structured configuration and metrics; open with a text editor |
| PNG / GIF | Static plot / animated schematic |
| `qpos`, `qvel` | Generalized positions / velocities |
| Yaw / pitch / roll | Turning left-right / tilting forward-back / leaning sideways |
| RMS error | Square root of the mean squared error; a typical error magnitude |
| Peak error | Largest absolute error; exposes brief excursions hidden by RMS |
| Seed | Number making a pseudorandom task draw repeatable |
| Paired trial | All compared methods receive the same sampled task conditions |
| Physics timestep | Here 0.002 s: 500 physics steps per simulated second |

Some internal values use radians. Convert with degrees = radians × 180 / pi. A metric ending `_rad` is not in degrees. The attention and full-body summaries already contain degree-labelled metrics.

Never compare the 0.864-degree supported-head mean directly with the 0.127-degree full-body mean as proof that standing is easier or more accurate: torso trajectories, timings and evaluation windows differ.

## 13. Try your own experiments safely and systematically

First reproduce defaults. Then change one variable at a time and preserve the original results.

The basic head program has a CLI. List options:

```text
uv run --locked --extra report python scripts/head_stabilization.py --help
```

Example: a new 30-degree, 1 Hz trial saved separately:

```text
uv run --locked --extra report python scripts/head_stabilization.py --torso-yaw-amplitude-deg 30 --frequency 1 --duration 6 --output-dir results/my_30deg_1hz
```

Example: compare a smaller feedback gain:

```text
uv run --locked --extra report python scripts/head_stabilization.py --gaze-gain 1 --output-dir results/my_gain_1
```

`--sample-period` changes CSV/plot decimation, not the physics integration step or metric sampling. It is not a way to make the physics run at a different rate.

The attention and whole-body scripts expose most experiment settings in source, not as CLI flags. Search for `common`, `CRITERIA`, `range(12)`, the ten-second loop and cue/push times. Back up source before editing. If changing cue times, update every associated metric window, animation label, report description and success criterion. Full-body contact checks currently rely on the pinned model's body IDs; do not substitute an arbitrary updated robot model without reviewing them.

To study robustness next, introduce a well-defined new condition (for example a longer trial or larger push), retain an unchanged baseline, log exact parameters and seeds, and report both failures and successes. Do not raise success thresholds merely to convert failed tests into passes without explaining that design change.

## 14. Troubleshooting

### uv is not recognized / command not found

Close and reopen the terminal after installing uv. Follow the installer's PATH instructions. On Windows, verify you are using PowerShell rather than pasting Unix commands into Command Prompt. If the network is managed by a school/company, use its permitted installation method.

### No pyproject.toml / cannot open scripts/...

You are probably in the wrong folder or viewing an unextracted ZIP. Use `Get-Location` and `Get-ChildItem` in PowerShell, or `pwd` and `ls` on macOS/Linux. The current folder should contain `pyproject.toml`, `uv.lock` and `scripts`.

### Wrong Python version

Use the Python installation/sync commands from step 5 and run via uv. Python 3.13+ does not satisfy the project's `<3.13` requirement. Never edit that requirement merely to suppress an error before checking package compatibility.

### Import errors, or ReportLab/pypdf disappeared

Use `uv sync --locked --extra report --python 3.12` again and include `--extra report` in `uv run` commands. Avoid mixing global pip, Conda and this project's environment. A uv command without the optional extra can synchronize an environment without report packages.

### Old or incompatible .venv

Close programs using it. Rename only the project `.venv` folder to `.venv_old`, then repeat step 5 to make a fresh isolated one. Preserve your source/results. Do not enable system-site-packages. The original machine's inherited Matplotlib packages caused an Axes3D warning, which is not a project requirement.

### Missing STL or XML asset

Check that the full `assets/microduck/assets/` directory transferred and contains 38 STL files. Do not flatten the folders. Run `build_head_rig.py` if only the generated head model is missing. Original full-body models must come from the archive, not that generator.

### Graphics/OpenGL errors

The provided experiments do not open a MuJoCo 3D viewer. They save Matplotlib plots and a schematic GIF; no `MUJOCO_GL` override is normally needed. First reproduce these without adding viewer/rendering code. If experimenting with a viewer later, consult MuJoCo's platform-specific Python viewer instructions; macOS passive viewers have additional launcher requirements.

### Animation seems slow

Allow it to finish. Use `--skip-animation` for numerical checks when no new GIF is needed. Open the saved GIF in a browser if your image app displays only its first frame.

### Report build cannot find a result file

Run attention_response.py and full_body_balance.py first. The report builder reads their current images/JSON. Keep the `report` and `results` folders in their original relative positions.

### Report exceeds ten pages

The builder raises an assertion. Shorten the source, reduce redundancy or deliberately adjust layout, then rebuild. Do not simply remove the limit check. Review page readability as well as page count.

### Results differ from the reference

Check your code/model files, parameters, seed list, Python and package versions first. Keep the supplied `uv.lock`; use `--locked`. Small platform-dependent numerical changes are possible, particularly near contact/threshold boundaries. A changed success count or large error difference deserves investigation. Do not manually edit summary JSON to match expected numbers.

## 15. Reproducibility record and completion checklist

For every new run, keep: source/archive version, `uv.lock`, Python and MuJoCo versions, operating system/CPU architecture, exact commands, changed parameters, seeds, output files and any warnings. Back up results before rerunning because the default output paths are overwritten.

Record dependencies:

```text
uv --version
uv run --locked --extra report python --version
uv pip freeze
```

To reproduce the whole sequence after setup:

```text
uv run --locked --extra report python scripts/build_head_rig.py
uv run --locked --extra report python scripts/head_stabilization.py
uv run --locked --extra report python scripts/verify_head_stabilization.py
uv run --locked --extra report python scripts/attention_response.py
uv run --locked --extra report python scripts/full_body_balance.py
uv run --locked --extra report python scripts/build_report.py
```

Mark complete only when all are true:

- Dependencies import successfully in a newly created environment.
- The generated head model exists and the nine-condition verification passes.
- New attention and whole-body summaries have been produced on your computer.
- You inspected both successful and failed cases, not just the headline pass count.
- Your GIF matches your recorded experiment settings.
- Your PDF opens, is at most ten pages and reflects the results you actually ran.
- You supplied real names/contributions and preserved upstream attribution/licenses.

This reproduces the current software proof of concept. A PPT, rendered full-body demonstration, hardware experiment and GPU-trained policy are separate work; they are not generated by this sequence.

## 16. Validation of this guide
On 14 November 2026, the source ZIP was extracted to a separate temporary Linux directory and installed using `uv sync --locked --extra report` in a new isolated Python 3.12.3 environment. Model generation, default head experiment, nine-condition verification, attention trials (`--skip-animation`), full-body trials and PDF generation all completed successfully. Attention and whole-body JSON summaries matched the reference results exactly on that host. GIF encoding was not repeated in this clean check; the supplied GIF was generated successfully earlier. Native Windows/macOS and another physical computer were not tested.
