# Bio-inspired Gaze Stabilization and Standing Control for Microduck
ELEC5621 Group Project | Technical report | 14 November 2026
Authors and contribution percentages: to be supplied by the group before submission.

## Abstract
This project develops the Attention and Response function of a companion robot: receive a simulated cue, orient the head toward a designated direction, and maintain gaze while preserving an upright posture. The design takes inspiration from avian neck-mediated gaze stabilization. It uses the public Microduck model in MuJoCo and separates controlled head/neck experiments from free-base whole-body standing experiments. A target-only controller, trunk compensation, and added gaze-error feedback are compared under paired conditions. Twelve supported-head trials give a mean stabilization RMS error of 0.864 degrees for the gaze-feedback controller, with all twelve meeting predefined acquisition and hold thresholds. A separate whole-body controller adds gravity compensation and ankle/hip attitude feedback while retaining original actuator force limits. Its measured results are generated directly from the accompanying JSON data. These experiments establish a limited simulation proof of concept; they do not establish hardware reliability, walking performance, or full three-dimensional biological equivalence.

## 1. Application and design specifications
The selected course function is Attention and Response. A preset simulation event represents the user cue; a direction in the world frame represents the user. Vision and speech recognition are outside the selected function. Head yaw is the controlled gaze variable. Neck pitch, head pitch and head roll remain actuated posture coordinates; the full model additionally contains ten leg joints and a floating base.

The supported experiment begins with one second of settling and a stationary trunk. At trial time 0.5 s the desired gaze changes by a signed 10–20 degrees. At 2 s a prescribed sinusoidal torso yaw begins. The response must acquire the target within 1 s, remain within 3 degrees for a full 0.2 s, then achieve hold RMS at most 3 degrees and peak error at most 6 degrees. Yaw must remain within its joint limits. These are project engineering criteria, not thresholds supplied by the course.

The whole-body experiment begins from the official STAND keyframe on a horizontal plane. The base remains free: there is no mocap support, weld or artificial restoring force. The head receives a target cue at 2 s. A horizontal trunk force, between -0.2 and 0.2 N, is applied for 0.1 s at 5 s. A ten-second stand must preserve base height of at least 75 mm and absolute roll/pitch at most 20 degrees, with no non-foot ground contact and no joint excursion beyond a 0.01 rad numerical tolerance. This deliberately broad standing criterion must not be confused with precise posture regulation.

---
## 2. Biological basis and related work
Gioanni [1] quantified optokinetic eye and head responses in pigeons and demonstrated that head motion contributes substantially to gaze stabilization. This supports treating the neck as an active gaze actuator rather than a passive mount. Gioanni [2] investigated vestibulo-ocular and closed-loop vestibulo-collic responses under head-fixed and head-free rotation, including conditions with and without visual surroundings. Together these experiments motivate combining body-motion compensation with a correction driven by gaze error.

Our implementation is an engineering abstraction of that coordination principle. It uses ideal simulator orientation rather than retinal slip or a physiological vestibular model. It does not reproduce neural dynamics, eye movements, frequency-dependent biological gains or sensory adaptation. The primary experimental evidence reviewed here concerns pigeons, not chickens; therefore the defensible description is avian-inspired gaze stabilization. The familiar chicken-head analogy motivates the concept but does not substitute for species-specific evidence. Access to the Gioanni papers here was limited to their indexed abstracts; conclusions are restricted accordingly.

Kajita et al. [3] generate biped walking patterns through ZMP preview control using future references and a simplified cart-table model. Their work explains why whole-body support must be considered independently of head tracking: an acceptable gaze trajectory does not guarantee contact stability. ZMP preview is suitable when footsteps and references are available, but requires a broader dynamics and trajectory framework than the current stationary task. We implement a simpler attitude-feedback stand controller, not Kajita's preview algorithm. We do not compute or claim ZMP margins.

The public Microduck repository [4] supplies articulated geometry, inertial parameters and position-actuator definitions, reducing the need to invent a robot. MuJoCo's documented contact formulation [5] provides the simulator basis; soft contact means finite penetration and numerical tolerances require explicit inspection. Neither source independently validates our controller or our hardware-level conclusions.

Compared approaches have distinct roles. Target-only positioning provides a transparent baseline but does not reject torso motion. Orientation compensation predicts the necessary counterrotation from body yaw, but cannot fully eliminate tracking dynamics. Gaze feedback corrects residual error, at the cost of dependence on sensing and gain selection. Learning-based control could broaden coverage, but is not required by the course and was not trained here. No GPU speedup or learned-policy performance is claimed.

---
## 3. Model, control architecture and implementation
The official Microduck model is pinned to revision 0daab160d3fb1c2cbaba16a4a19052f36709dd9e. The repository model and STL licenses are preserved under assets/microduck; SOURCE.md records modifications. Model XML uses Apache 2.0 terms and mesh assets have CC BY-NC-SA 4.0 terms as recorded upstream. Our contributions are the subsystem transformation, controllers, cue sequencing, paired evaluation, safeguards and report generation.

For controlled head experiments, a generated rig retains the four actual head/neck joints and removes the leg branches. A mocap trunk prescribes orientation. Camera gaze is the azimuth of its world-frame optical axis, using the negative local Z direction. Body Euler yaw alone is insufficient because the articulated head frame has nontrivial orientation. A finite-difference calibration estimates head-yaw joint gain g near the reference pose.

Let e be wrapped gaze yaw minus desired yaw, and delta_psi be trunk yaw relative to its reference. The target-only position command is q_ref + target_offset/g. Compensation subtracts delta_psi/g. The optimized controller additionally subtracts K_g e/g, with K_g=2. Commands are clipped to head-yaw joint limits. All cases receive the same target and torso motion. Ideal state measurements and the original actuator parameters are used.

For full-body standing, position-actuator targets are adjusted to request additional bounded torque: u = q_ref + (bias - 0.1*q_velocity + attitude_correction)/k_position. Bias is the simulator generalized bias force at actuated coordinates. Ankle corrections use world-Y joint-axis projection times pitch + 0.1*base_pitch_rate; hip-roll corrections use world-X axis projection times -roll - 0.1*base_roll_rate. These empirical gains were selected after a small nominal five-second tuning sweep, so evaluation results are not independent evidence of globally optimal gains. Original actuator control ranges and force limits remain active. A position target may lie outside a joint's angular range to request torque; measured joint states, rather than target values, are checked against joint limits.

The full-body head controller adds target offset, trunk yaw compensation and gaze feedback. The cue is delayed until 2 s to allow the standing transient. This experiment uses actual free-base motion; its conditions differ from the prescribed-torso experiment and their gaze RMS values must not be pooled.

---
## 4. Experimental methods and results
All simulation uses a 2 ms step. Derived poses are refreshed after integration so joint positions and gaze refer to the same state. Metrics use every physics step. CSV decimation in the original stabilization program affects saved plotting samples only. Cue decisions use step-start time; rows describe step-end state. A 0.5 s cue first appears in the 0.502 s row.

The original parameter sweep covers torso amplitudes 10, 20 and 30 degrees at 0.25, 0.5 and 1 Hz. Nine comparisons show lower RMS for gaze feedback than compensation alone. Input validation, finite values, yaw limits and metric invariance to CSV sampling were checked. This sweep explores parameters; it is not a repeated-sampling reliability study.

The attention experiment uses seeds 0–11 to draw twelve tasks from a fixed distribution. Target magnitude is uniform 10–20 degrees with random sign, torso amplitude uniform 10–20 degrees, and frequency uniform 0.25–0.5 Hz. Every controller receives the same draw. Acquisition checks include the full 0.200 s interval; a regression check rejects a 0.198 s near-miss. Hold statistics use times strictly after disturbance onset.

Observed supported-head results: target-only succeeds in 0/12 tasks, with mean hold RMS 10.967 degrees and sample standard deviation 1.909 degrees. Compensation succeeds in 10/12, with RMS 2.603 degrees and standard deviation 0.507 degrees. Added gaze feedback succeeds in 12/12, with RMS 0.864 degrees and standard deviation 0.166 degrees. Its largest hold peak across these trials is 2.111 degrees. Twelve successes constitute finite evidence within the selected distribution, not a population guarantee.

The whole-body comparison uses twelve paired seeds, ten-second trials and the same cue/push schedule for both methods. Baseline failure before the cue means repeated baseline traces are identical; they must not be represented as twelve different disturbance responses. Per-trial results, including any failed checks, are included in the automatically generated results table on the next page.

---
## 5. Interpretation, limitations and iteration
The supported rig isolates the contribution of head control. It cannot establish leg stability, base dynamics or complete inertial disturbance rejection: prescribing mocap poses does not provide a physically driven base with fully consistent velocity and acceleration coupling. The separate whole-body experiment addresses free-base standing, but does not demonstrate robustness over the full amplitude/frequency sweep or locomotion.

The full-body controller has empirical gains and perfect simulator state. Its finite trials test small horizontal forces, target variation and contact evolution, not unknown terrain, large impulses, sensor delay, calibration errors or hardware actuator bandwidth. The standing tilt threshold is permissive, and peak tilt must be reported alongside pass counts. Joint-limit checks use a declared tolerance because MuJoCo constraints are soft. Non-foot contacts are explicitly counted; support-polygon and contact-force margins remain unmeasured. Longer-duration drift and repeated interaction cycles are also untested.

The head result is yaw stabilization, not stabilization of all position and orientation coordinates. A practical extension would introduce realistic IMU and gaze estimates, sensor noise and delay, smoothly planned target transitions, gain scheduling and three-dimensional gaze error. For standing, the next step is systematic contact-aware control with center-of-mass/support-region metrics, stricter posture targets and a larger independently held-out perturbation set. A model-predictive or ZMP-based controller should be compared only after its assumptions and support geometry are defined.

The current demonstration includes measured-angle schematic animation and full-body trajectory plots. The schematic should be labelled as such in the presentation; it does not show a rendered free-standing robot. A recorded or live full-robot demonstration remains a presentation preparation item. Group names, contribution percentages and final submission checks must be completed by the actual group.

## 6. Reproducibility and conclusion
Run uv sync, then scripts/build_head_rig.py, scripts/head_stabilization.py, scripts/verify_head_stabilization.py, scripts/attention_response.py and scripts/full_body_balance.py using the project Python environment. Results are stored beneath results/. The report builder reads those results and produces this PDF. The source model is preserved; scripts apply control at runtime. No hardware changes or reinforcement-learning training are part of this experiment.

The project provides a cue-triggered gaze-control proof of concept and an initial free-base standing extension. Supported-head comparisons show a measurable benefit from added gaze feedback under the defined conditions. Whole-body evidence must be interpreted using its own criteria and reported peak posture deviations. The contribution is a reproducible and explicitly bounded integration study, with documented remaining work toward a deployable companion robot.

---
## References
[1] H. Gioanni. Stabilizing gaze reflexes in the pigeon (Columba livia). I. Horizontal and vertical optokinetic eye (OKN) and head (OCR) reflexes. Experimental Brain Research 69, 567–582, 1988. DOI: 10.1007/BF00247310. https://pubmed.ncbi.nlm.nih.gov/3371439/

[2] H. Gioanni. Stabilizing gaze reflexes in the pigeon (Columba livia). II. Vestibulo-ocular (VOR) and vestibulo-collic (closed-loop VCR) reflexes. Experimental Brain Research 69, 583–593, 1988. DOI: 10.1007/BF00247311. https://pubmed.ncbi.nlm.nih.gov/3259511/

[3] S. Kajita, F. Kanehiro, K. Kaneko, K. Fujiwara, K. Harada, K. Yokoi and H. Hirukawa. Biped Walking Pattern Generation by using Preview Control of Zero-Moment Point. IEEE ICRA, 1620–1626, 2003. DOI: 10.1109/ROBOT.2003.1241826. https://mzucker.github.io/swarthmore/e91_s2013/readings/kajita2003preview.pdf

[4] Pollen Robotics. microduck_rl, develop branch, pinned revision documented above. https://github.com/pollen-robotics/microduck_rl/tree/0daab160d3fb1c2cbaba16a4a19052f36709dd9e

[5] MuJoCo documentation. Computation: soft contact model and dynamics. https://mujoco.readthedocs.io/en/stable/computation/index.html (accessed 14 November 2026).

[6] ELEC5621_Project.pdf, course-provided group project specification, four pages, 2026.
