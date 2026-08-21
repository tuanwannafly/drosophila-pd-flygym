# Project Context

## Objective

This repository supports an in-silico research prototype for simulating
Drosophila melanogaster locomotion phenotypes with FlyGym, NeuroMechFly, and
MuJoCo. The long-term research direction is to build a reproducible
unperturbed baseline, introduce controlled motor or controller perturbations,
quantify gait phenotypes, and only then explore Parkinson's-disease-like
perturbation scenarios.

This is a computational simulation project. Simulation output must not be
presented as direct evidence from real Drosophila. Biological validation can be
claimed only when supported by external experimental evidence.

## Software Stack

- Python target: 3.12
- FlyGym target: 2.1.0
- NeuroMechFly as the primary fly model
- MuJoCo target: 3.9.0
- Google Colab for execution and prototyping
- GitHub as the source of truth
- Codex for implementation, debugging, and documentation support

## Current Scientific Checkpoint

Milestone C is complete and frozen. The project now has a reproducible
unperturbed simulation baseline that creates the official FlyGym locomotion fly,
adds position and adhesion actuators through the canonical baseline pipeline,
runs a deterministic flat-ground simulation, and records derived locomotion
metrics.

Milestone C is an unperturbed simulation baseline only. It is not biological
validation, not a Parkinson's disease model, and not evidence from real
Drosophila.

Milestone E5 is the latest frozen computational checkpoint. It validates
preregistered computational reversibility of the frozen E3/E4 candidate and
records software/simulation behavior only.

Milestone E4 is the current literature-grounded concordance layer. It evaluates
the frozen E3 computational phenotype against selected adult Drosophila dopamine
and alpha-synuclein walking literature using qualitative endpoint mapping only.
E4 does not tune the frozen candidate, does not run a new parameter search, does
not implement rescue experiments, and does not validate a Parkinson's disease
model.

Milestone E5 is FROZEN - PREREGISTERED COMPUTATIONAL REVERSIBILITY. It tests
whether fixed, preregistered partial returns of the frozen E3/E4 computational
candidate's two proxy parameters move supported locomotor-output endpoints back
toward the unperturbed baseline. E5 does not tune the candidate, does not run a
rescue parameter sweep, does not implement pharmacology, and does not claim
dopaminergic, mechanistic, biological, or Parkinson's disease rescue.

Milestone E6 is FROZEN - REPRODUCIBLE EVIDENCE SYNTHESIS. It is an evidence-only
analysis layer that reads the frozen C, D, E1, E2, E3, E4, and E5 JSON reports,
validates their schemas, provenance, pass states, and frozen candidate identity,
and generates reproducible CSV summaries and matplotlib figures. E6 does not
run FlyGym or MuJoCo, change simulation behavior, tune parameters, or establish
biological validation.

Milestone 8B is complete and frozen. The project crossed the joint
materialization boundary exactly once through a canonical, explicitly named
software gate before moving on to the unperturbed locomotion baseline.

Milestone 8B supersedes the historical Session 02 Blocks 8.14-8.19 notebook
sequence. Those historical cells remain important research records, but their
scientifically relevant anatomy/materialization observations are now represented
by repository code and the frozen JSON evidence report.

Verified Block 8.12 invariants:

- Fly object type: `flygym.compose.fly.neuromechfly.NeuroMechFly`
- `fly.skeleton is None`
- `add_joints()` has not been called
- Body segments: 69
- Anatomical joints: 68
- JointDOFs: 204
- Axis order: `AxisOrder.PITCH_ROLL_YAW`
- Pitch DOFs: 68
- Roll DOFs: 68
- Yaw DOFs: 68
- LF leg JointDOFs: 24
- LM leg JointDOFs: 24
- LH leg JointDOFs: 24
- RF leg JointDOFs: 24
- RM leg JointDOFs: 24
- RH leg JointDOFs: 24
- Non-leg JointDOFs: 60
- MJCF body mapping: 69/69
- Missing parent MJCF bodies for JointDOFs: 0
- Missing child MJCF bodies for JointDOFs: 0
- JointDOF to MJCF joint mapping: 0, expected before materialization
- JointDOF to neutral angle mapping: 0, expected before materialization
- Actuator mappings: 0, expected before materialization
- JointDOF names are unique: 204
- JointDOF name round-trip failures: 0

The empty JointDOF, neutral-angle, and actuator mappings are expected before
joint materialization. They must not be interpreted as errors. These Block 8.12
invariants define the frozen pre-materialization state used by Milestone 8B.

## Block 8.12 Reproduction Status

On August 11, 2026, Block 8.12 was independently reproduced from a fresh
Google Colab runtime using repository code:

```bash
python scripts/audit_block_8_12.py --output results/baseline/block_8_12_audit.json
```

Observed clean-runtime versions were Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. The generated JSON report returned `overall_pass = true`,
`skeleton_before_is_none = true`, `skeleton_after_is_none = true`, MJCF body
mapping total 69, missing parent MJCF bodies 0, and missing child MJCF bodies 0.
The other documented Block 8.12 invariants also passed.

This reproduction validates the repository's non-mutating software/anatomy audit
only. It does not validate a Parkinson's disease model, locomotor biology, or
evidence from real flies.

## Milestone 8B Reproduction Status

On August 11, 2026, Milestone 8B was independently reproduced from a fresh
Google Colab runtime using repository code:

```bash
python scripts/run_joint_materialization_milestone.py --output results/baseline/milestone_8b_materialization.json
```

Observed clean-runtime versions were Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. The generated JSON report returned `overall_pass = true` and all
48 documented checks passed.

Verified Milestone 8B transition:

- Pre-state `fly.skeleton is None`: true
- Pre-state MJCF root joints: 0
- Materialization gate used: true
- `add_joints()` executed only through `materialize_joints_explicit_gate`
- Post-state skeleton is materialized as `flygym.anatomy.Skeleton`
- Post-state MJCF root joints: 204
- JointDOF to MJCF joint mapping: 204
- JointDOF to neutral-angle mapping: 204
- Actuator mappings: 0
- MJCF root actuators: 0
- Second materialization attempt rejected: true

This reproduction validates FlyGym/NeuroMechFly joint materialization and
post-materialization anatomy mappings only. It does not create actuators, run
locomotion, implement controllers, or validate a Parkinson's disease model.

## Milestone C Reproduction Status

On August 11, 2026, Milestone C was independently reproduced from a fresh
Google Colab runtime using repository code:

```bash
python scripts/run_healthy_baseline.py --config configs/experiments/healthy_baseline.yaml --output results/baseline/healthy_baseline.json
```

Observed clean-runtime versions were Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. The generated JSON report returned `overall_pass = true`.

Verified Milestone C unperturbed baseline summary:

- Requested duration: 0.5 s
- Timestep: 0.0001 s
- Simulation steps: 5000
- Position actuators: 42
- Adhesion actuators: 6
- Compiled MuJoCo control dimension (`nu`): 48
- Planar displacement: 6.284186050286936 mm
- Mean planar speed: 12.568372100573873 mm/s
- Heading yaw change: 0.2342730946151257 rad
- Thorax height min/mean/final: 0.7660532202481788 /
  0.946592192150494 / 1.0115140447050612 mm
- Raw observations and derived metrics finite: true

This reproduction validates only the deterministic unperturbed FlyGym
simulation pipeline and derived software metrics. It does not establish
biological realism or disease relevance.

## Materialization Boundary And Current Stop Point

Milestone 8B is the authorized materialization boundary:

- `fly.add_joints(...)` may be called only inside
  `materialize_joints_explicit_gate`.
- Do not assign `fly.skeleton` manually.
- Repository anatomy/materialization audit code must not call `add_joints()`
  from any other code path.

Before the Milestone 8B gate:

- Do not call `fly.add_joints(...)`.
- Do not assign `fly.skeleton`.
- Do not intentionally mutate the MJCF model.
- Do not create actuators, sites, or sensors on the live model.

After the Milestone 8B gate, `fly.skeleton`, MJCF joints, joint mappings, and
neutral-angle mappings are materialized. Actuator mappings and MJCF actuators
remain empty by design for Milestone 8B.

Milestone C is the authorized unperturbed locomotion baseline. It creates the
official FlyGym locomotion fly, position actuators, adhesion actuators,
`FlatGroundWorld`, and `Simulation` through the canonical baseline pipeline.

Milestone D is complete and frozen. The controlled perturbation framework runs
paired baseline-vs-perturbed simulations from fresh FlyGym/MuJoCo state while
holding random seed, duration, timestep, world, spawn, baseline controller,
skeleton, actuator architecture, and metric definitions constant.

Milestone D is a controlled software/simulation perturbation framework only. It
does not define a Parkinson's disease mechanism, validate disease biology, or
map a controller parameter directly to dopamine or any other biological
mechanism.

## Milestone D Reproduction Status

On August 11, 2026, Milestone D was independently reproduced from a fresh
Google Colab runtime using repository code:

```bash
python scripts/run_perturbation_experiment.py --baseline-config configs/experiments/healthy_baseline.yaml --perturbation-config configs/experiments/perturbations/identity.yaml --output results/perturbations/identity.json

python scripts/run_perturbation_experiment.py --baseline-config configs/experiments/healthy_baseline.yaml --perturbation-config configs/experiments/perturbations/action_scale_080.yaml --output results/perturbations/action_scale_080.json
```

Observed clean-runtime versions were Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. Both evidence files report git commit
`f886c204d8ad3a95dcd953418a8f9df51927137f`.

Verified Milestone D identity gate:

- Evidence path: `results/perturbations/identity.json`
- `overall_pass = true`
- `identity_equivalence_pass = true`
- Controlled variables match: true
- Fresh fly/world/simulation per condition: true
- Baseline and identity step counts: 5000 / 5000
- Identity comparison deltas: zero across recorded scalar and adhesion metrics
- Action transformation: identity with transform error 0.0

Verified Milestone D action-scale perturbation:

- Evidence path: `results/perturbations/action_scale_080.json`
- `overall_pass = true`
- Perturbation type: `global_action_scale`
- Scale: 0.8
- Intervention target: controller joint-angle commands
- Action shape: 5000 x 42
- Joint-angle transform error: 0.0
- Adhesion commands preserved: true
- Controlled variables match: true
- Fresh fly/world/simulation per condition: true

Observed action-scale simulation response relative to the paired baseline:

- Planar displacement delta: -0.6714494674507625 mm
- Mean planar speed delta: -1.342898934901525 mm/s
- Heading yaw-change delta: 0.03061053070618347 rad
- Body height minimum delta: 0.3917972226323848 mm
- Body height mean delta: 0.5321613121790706 mm
- Body height range delta: -0.0011024944162713046 mm
- Joint action mean delta: -0.06393024147301052
- Joint action absolute mean delta: -0.20487402724275616
- Adhesion duty-factor deltas: 0.0 for all legs
- Adhesion transition-count deltas: 0 for all legs

The action-scale experiment is a generic software/simulation perturbation. It
is not a Parkinson's disease model and is not biological validation.

## Milestone E0/E1 Working Hypothesis

Milestone E0/E1 begins parameter-response characterization before choosing any
PD-like computational phenotype. The current working hypothesis is that
Drosophila locomotor dysfunction relevant to later Parkinson-related modeling
may be explored phenomenologically through impairments in:

- locomotor motor vigor or output
- locomotor coordination

These are computational hypotheses, not direct mechanistic dopamine mappings.
The repository must continue to distinguish biological evidence, computational
hypothesis, simulation intervention, and observed simulation response.

Milestone E0/E1 uses two generic perturbation families:

- `motor_vigor_proxy`: global scaling of the 42 joint-angle controller commands
  with scale values 1.00, 0.90, 0.80, 0.70, and 0.60.
- `coordination_proxy`: scaling of FlyGym CPG inter-leg coupling weights with
  scale values 1.00, 0.75, 0.50, 0.25, and 0.00.

For both families, scale 1.00 is the exact baseline-equivalent control value.
These parameter sweeps are not disease-severity series.

Motor-vigor and coordination perturbations are phenomenological computational
proxies. They are not direct simulations of dopamine concentration or
dopaminergic neuron loss, and they do not validate a Parkinson's disease model.

The canonical Milestone E0/E1 sweep command is:

```bash
python scripts/run_parameter_sweep.py --baseline-config configs/experiments/healthy_baseline.yaml --sweep-config configs/experiments/sweeps/milestone_e1.yaml --output results/sweeps/milestone_e1.json
```

## Milestone E1 Reproduction Status

Milestone E1 is complete and frozen as parameter-response characterization.

On August 11, 2026, Milestone E1 was independently reproduced from a fresh
Google Colab runtime using repository code:

```bash
python scripts/run_parameter_sweep.py --baseline-config configs/experiments/healthy_baseline.yaml --sweep-config configs/experiments/sweeps/milestone_e1.yaml --output results/sweeps/milestone_e1.json
```

Observed clean-runtime versions were Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. The evidence file reports git commit
`7cb2ed580b8eabb6a363b27f481564751eeb9e48` and `overall_pass = true`.

Verified Milestone E1 sweep summary:

- Evidence path: `results/sweeps/milestone_e1.json`
- Conditions completed: 10 / 10
- Completed conditions passed: true
- Baseline-equivalent conditions passed: true
- Motor-vigor proxy scales: 1.00, 0.90, 0.80, 0.70, 0.60
- Coordination proxy coupling scales: 1.00, 0.75, 0.50, 0.25, 0.00
- Controlled variables preserved for every condition: true
- Raw observations and derived metrics finite for every condition: true

Observed Milestone E1 response-surface findings:

- Motor-vigor scaling produced a graded reduction in planar displacement and
  mean planar speed across the configured scale series.
- Joint-action absolute mean followed commanded motor-vigor scaling exactly:
  0%, -10%, -20%, -30%, and -40% relative to the unperturbed baseline.
- Body-height response was nonlinear: height mean increased as motor-vigor
  scale decreased, while height range was non-monotonic.
- CPG coupling reduction had modest displacement/speed effects at intermediate
  values 0.75, 0.50, and 0.25.
- Near-zero CPG coupling produced a large locomotion loss and large yaw
  deviation: displacement delta -45.809430686563735% and yaw-change relative
  delta 850.3387842988586% versus baseline.

These are simulation response surfaces only. No E1 parameter value is currently
designated as Parkinson's disease, dopamine depletion, neuron-loss percentage,
disease stage, or biological severity.

## Milestone E2 Reproduction Status

Milestone E2 is FROZEN — COMBINED PHENOTYPE CHARACTERIZATION.

On August 11, 2026, Milestone E2 was independently reproduced from a fresh
Google Colab runtime using repository code:

```bash
python scripts/run_combined_phenotype_sweep.py --baseline-config configs/experiments/healthy_baseline.yaml --sweep-config configs/experiments/sweeps/milestone_e2.yaml --output results/sweeps/milestone_e2_combined.json
```

Observed clean-runtime versions were Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. The evidence file reports git commit
`433269ed11e0475eb973b62d31f469d66843872f` and `overall_pass = true`.

Verified Milestone E2 sweep summary:

- Evidence path: `results/sweeps/milestone_e2_combined.json`
- Conditions completed: 9 / 9
- Completed conditions passed: true
- Control-equivalent condition passed: true
- Controlled variables preserved for every completed condition: true
- Fresh simulation state per condition declared: true
- Raw observations and derived metrics finite for every condition: true

Milestone E2 composes two generic computational proxies:

- `coordination_proxy`: CPG coupling-weight scale.
- `motor_vigor_proxy`: global joint-angle action scale.

The E2 implementation records controller-stage and action-stage transformations
separately, preserves controlled variables except for the declared proxy values,
adds trajectory efficiency when derivable from thorax-position samples, and
reports interaction residuals for combined conditions.

Observed Milestone E2 condition summary:

| condition | motor | coupling | displacement mm | speed mm/s | yaw rad | height mean mm | action abs mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| control_motor_100_coupling_100 | 1.0 | 1.0 | 6.284186050286936 | 12.568372100573873 | 0.2342730946151257 | 0.946592192150494 | 1.0243701362137825 |
| motor_080_coupling_100 | 0.8 | 1.0 | 5.612736582836174 | 11.225473165672348 | 0.26488362532130916 | 1.4787535043295645 | 0.8194961089710263 |
| motor_070_coupling_100 | 0.7 | 1.0 | 5.268050612232854 | 10.536101224465709 | 0.11859624957082766 | 1.7640121538755738 | 0.7170590953496476 |
| motor_060_coupling_100 | 0.6 | 1.0 | 4.665347652380944 | 9.330695304761887 | 0.12149833837745547 | 2.0254362305602083 | 0.6146220817282696 |
| motor_100_coupling_075 | 1.0 | 0.75 | 6.21723627703009 | 12.43447255406018 | 0.29121506035623623 | 0.94667094441612 | 1.0243119639852822 |
| motor_100_coupling_050 | 1.0 | 0.5 | 6.105537853973774 | 12.211075707947549 | 0.33130987292379543 | 0.9564334845117194 | 1.0244046906374453 |
| combined_motor_080_coupling_075 | 0.8 | 0.75 | 5.513499489822533 | 11.026998979645066 | 0.30259921850584254 | 1.478905964396374 | 0.8194495711882258 |
| combined_motor_070_coupling_075 | 0.7 | 0.75 | 5.136531853151933 | 10.273063706303866 | 0.15663928641475375 | 1.7535528444304547 | 0.7170183747896974 |
| combined_motor_070_coupling_050 | 0.7 | 0.5 | 5.029479715627041 | 10.058959431254083 | 0.2533262746314835 | 1.742194548438357 | 0.7170832834462115 |

Observed combined-condition results:

- Motor 0.8 / coupling 0.75: displacement 5.513499489822533 mm, mean speed
  11.026998979645066 mm/s, yaw 0.30259921850584254 rad, height mean
  1.478905964396374 mm, action absolute mean 0.8194495711882258.
- Motor 0.7 / coupling 0.75: displacement 5.136531853151933 mm, mean speed
  10.273063706303866 mm/s, yaw 0.15663928641475375 rad, height mean
  1.7535528444304547 mm, action absolute mean 0.7170183747896974.
- Motor 0.7 / coupling 0.5: displacement 5.029479715627041 mm, mean speed
  10.058959431254083 mm/s, yaw 0.2533262746314835 rad, height mean
  1.742194548438357 mm, action absolute mean 0.7170832834462115.

Observed interaction findings:

- Speed and displacement interaction effects were mostly close to additive for
  the three combined conditions.
- Directional/yaw effects were more nonlinear: motor 0.8 / coupling 0.75 was
  sub-additive, motor 0.7 / coupling 0.75 was super-additive, and motor 0.7 /
  coupling 0.5 showed direction reversal relative to the additive expectation.
- Motor 0.8 / coupling 0.75 is a leading computational candidate for further
  validation because it combines reduced locomotor output with continued stable
  simulation behavior and moderate directional change.

Milestone E2 does not choose a final Parkinson's-disease-like condition, does
not implement rescue experiments, and does not map any parameter value to
dopamine concentration, dopaminergic neuron loss, disease stage, or biological
severity.

## Milestone E3 Reproduction Status

Milestone E3 is FROZEN - MULTI-SEED ROBUSTNESS VALIDATION.

On August 11, 2026, Milestone E3 was independently reproduced from a fresh
Google Colab runtime using repository code:

```bash
python scripts/run_candidate_robustness.py --baseline-config configs/experiments/healthy_baseline.yaml --validation-config configs/experiments/validation/milestone_e3.yaml --output results/validation/milestone_e3_candidate_robustness.json
```

Observed clean-runtime versions were Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. The evidence file reports git commit
`730ab3acd8e5535b93f320a62c19080feca0448f`, `overall_pass = true`, and
robustness classification `ROBUST`.

Verified Milestone E3 summary:

- Evidence path: `results/validation/milestone_e3_candidate_robustness.json`
- Paired seeds completed: 5 / 5
- Seeds: 0, 1, 2, 3, and 4
- Duration: 1.0 s
- Fresh fly/world/simulation per condition declared: true
- Same seed within every baseline/candidate pair: true
- Required observations and metrics finite: true
- Controlled variables preserved: true
- Candidate transformation validated: true
- Displacement delta negative for all 5 seeds: true
- Speed delta negative for all 5 seeds: true

The frozen candidate differs from the paired baseline only by the E2 proxy
values:

- `motor_scale = 0.8`
- `coupling_scale = 0.75`

These parameters were selected before E3 execution from Milestone E2
characterization. No post-hoc tuning is permitted inside E3.

Observed aggregate Milestone E3 findings:

- Planar displacement mean: baseline 13.751281674590993 mm, candidate
  12.302040063313584 mm, mean relative delta -10.53649998704906%.
- Mean planar speed: baseline 13.751281674590993 mm/s, candidate
  12.302040063313584 mm/s, mean relative delta -10.53649998704906%.
- Planar path length mean: baseline 19.31485503067457 mm, candidate
  17.308442670909542 mm, mean relative delta -10.386359062038664%.
- Trajectory efficiency mean: baseline 0.7119806020699851, candidate
  0.7107636180753024, mean relative delta -0.16292589177790413%.
- Joint action absolute mean: baseline 1.0256368082597096, candidate
  0.820559121832831, mean relative delta -19.995156821323032%.
- Body height mean: baseline 0.9465522152698778 mm, candidate
  1.4910686043526398 mm.
- Absolute yaw-change mean: baseline 0.10385794490113649 rad, candidate
  0.21120580249246884 rad.

Observed variability and confounds:

- Displacement and speed reduction were directionally consistent across all 5
  seeds.
- Trajectory-efficiency delta was mixed across seeds: 3 negative and 2
  positive.
- Absolute-yaw-change delta was positive in 4 / 5 seeds.
- Body-height response remains an important confound and phenotype component.

E3 PASS semantics are software/simulation only: all paired simulations completed,
required observations and metrics were finite, controlled variables were
preserved, candidate transformations were validated, and aggregate reporting was
produced. PASS does not require a desired biological phenotype.

The `ROBUST` classification means computational/software robustness under the
tested seeds only. It does not mean biological robustness, statistical
significance, Parkinson's disease validation, disease severity, dopamine
depletion, or mechanistic validation.

Milestone E3 does not introduce new disease mechanisms, does not implement
rescue experiments, and does not establish a mechanistic or biologically
validated Parkinson's disease model.

## Milestone E4 Concordance Status

Milestone E4 is LITERATURE-GROUNDED PHENOTYPE CONCORDANCE.

E4 uses the frozen E3 evidence only:

```bash
python scripts/run_phenotype_concordance.py --output results/validation/milestone_e4_concordance.json
```

The curated evidence matrix is
`docs/scientific/e4_evidence_matrix.yaml`. The generated report is
`results/validation/milestone_e4_concordance.json`.

E4 records adult walking evidence separately from larval or non-adult evidence.
The current E4 matrix contains primary adult evidence only:

- Riemensperger et al. 2011, DOI `10.1073/pnas.1010930108`, PMID
  `21187381`: neural dopamine-deficient adult flies showed reduced walking
  speed and covered distance relative to control contexts.
- Chen et al. 2014, DOI `10.1111/gbb.12172`, PMID `25113870`: old adult A30P
  alpha-synuclein flies showed reduced total moving distance, distance per
  movement, walking velocity, and angular velocity, with age dependence.

Endpoint concordance is qualitative and directional only. E4 records:

- Walking speed / velocity -> `mean_planar_speed_mm_s`: CONCORDANT.
- Covered distance / total moving distance -> `planar_path_length_mm`, with
  `planar_displacement_mm` as a supplemental metric: CONCORDANT.
- Distance per movement: NOT_COMPARABLE because E3 does not segment movement
  bouts.
- Angular velocity: NOT_COMPARABLE because E3 yaw change is not angular
  velocity.
- Centrophobism, climbing, pause/freezing: NOT_COMPARABLE or NOT AVAILABLE with
  the current flat-ground walking report.
- Thorax/body height: INSUFFICIENT_EVIDENCE for Parkinson interpretation in the
  selected literature set.

The generated E4 report returns `overall_pass = true` for schema and scientific
boundary checks and proposes `PARTIAL_PHENOTYPE_CONCORDANCE`. This means only
that the frozen E3 candidate's reduced locomotor output is directionally
consistent with selected adult walking endpoints while unsupported endpoints are
preserved. It does not mean biological validation, statistical significance,
dopamine depletion, disease severity, or mechanistic equivalence.

The frozen candidate remains unchanged:

- `motor_scale = 0.8`
- `coupling_scale = 0.75`

No E4 parameter tuning or direct numeric calibration is permitted.

## Milestone E5 Reproduction Status

Milestone E5 is FROZEN - PREREGISTERED COMPUTATIONAL REVERSIBILITY.

On August 11, 2026, Milestone E5 was independently reproduced from a fresh
Google Colab runtime using repository code:

```bash
python scripts/run_computational_rescue.py \
  --baseline-config configs/experiments/healthy_baseline.yaml \
  --validation-config configs/experiments/validation/milestone_e5.yaml \
  --output results/validation/milestone_e5_computational_rescue.json
```

Observed clean-runtime versions were Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. The evidence file reports git commit
`7cffac001488589d089bc49266aa103e7458f476`, timestamp
`2026-08-11T13:32:09.675748+00:00`, and `overall_pass = true`.

Verified Milestone E5 design:

- Evidence path: `results/validation/milestone_e5_computational_rescue.json`
- Seeds: `[0, 1, 2, 3, 4]`
- Duration: 1.0 s
- Conditions per seed: 6
- Total condition runs: 30
- Completed condition runs: 30 / 30
- Completed conditions passed: true
- Controlled variables preserved: true
- Required observations and derived metrics finite: true
- Fresh fly/world/simulation per condition declared: true
- No arbitrary recovery threshold introduced: true
- Post-hoc tuning forbidden: true
- Biological rescue claim forbidden: true
- Full computational restoration reference equivalent to control: true

The fixed preregistered condition matrix is:

- `control`: `motor_scale = 1.0`, `coupling_scale = 1.0`
- `impaired_candidate`: `motor_scale = 0.8`, `coupling_scale = 0.75`
- `motor_partial_rescue`: `motor_scale = 0.9`, `coupling_scale = 0.75`
- `coordination_partial_rescue`: `motor_scale = 0.8`,
  `coupling_scale = 0.875`
- `combined_partial_rescue`: `motor_scale = 0.9`,
  `coupling_scale = 0.875`
- `full_computational_restoration_reference`: `motor_scale = 1.0`,
  `coupling_scale = 1.0`

The midpoint values were preregistered before execution:

- `(0.8 + 1.0) / 2 = 0.9`
- `(0.75 + 1.0) / 2 = 0.875`

Primary endpoints are `mean_planar_speed_mm_s` and `planar_path_length_mm`.
For metrics expected to decrease in the impaired candidate, E5 reports the
computational recovery fraction:

```text
(rescue - impaired) / (control - impaired)
```

Primary endpoint aggregate findings:

| condition | endpoint | control mean | impaired mean | condition mean | recovery fraction | direction count | no-farther count | classification |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `motor_partial_rescue` | speed | 13.751281674590993 | 12.302040063313584 | 12.798554263221726 | 0.34260277654496735 | 5 / 5 | 5 / 5 | `DIRECTIONALLY_RESCUED` |
| `motor_partial_rescue` | path length | 19.31485503067457 | 17.308442670909542 | 18.06483724383281 | 0.3769885932181204 | 5 / 5 | 5 / 5 | `DIRECTIONALLY_RESCUED` |
| `coordination_partial_rescue` | speed | 13.751281674590993 | 12.302040063313584 | 12.38638348376136 | 0.05819831544405736 | 4 / 5 | 4 / 5 | `MIXED` |
| `coordination_partial_rescue` | path length | 19.31485503067457 | 17.308442670909542 | 17.32301662767562 | 0.007263689687290947 | 3 / 5 | 3 / 5 | `MIXED` |
| `combined_partial_rescue` | speed | 13.751281674590993 | 12.302040063313584 | 12.823982404294824 | 0.36014860249643493 | 5 / 5 | 5 / 5 | `DIRECTIONALLY_RESCUED` |
| `combined_partial_rescue` | path length | 19.31485503067457 | 17.308442670909542 | 18.018699776028235 | 0.35399358544714715 | 5 / 5 | 5 / 5 | `DIRECTIONALLY_RESCUED` |

The `full_computational_restoration_reference` condition is classified as a
reference, not a rescue condition. It reproduced the unperturbed control within
the declared deterministic tolerances for every seed.

Motor-axis restoration accounts for most of the primary locomotor recovery
observed in E5; adding partial coordination restoration produces modest and
endpoint-dependent additional effects. This interpretation is supported by both
primary endpoints. Compared with `motor_partial_rescue`,
`combined_partial_rescue` increased mean speed by only
0.025428141073097876 mm/s and recovery fraction by 0.017545825951467586, but
decreased mean path length by 0.04613746780457362 mm and recovery fraction by
0.02299500777097324. Combined partial restoration is therefore not universally
superior to motor-axis partial restoration.

Important secondary endpoint findings and confounds:

- Planar displacement mirrored mean speed because duration was fixed at 1.0 s.
- Trajectory-efficiency recovery fractions were denominator-sensitive because
  control and impaired aggregate means differed by only about 0.001216984. The
  per-seed directions were mixed, including recovery fractions below 0 and
  above 1.
- Absolute yaw-change responses were nonlinear. Coordination-only partial
  restoration had aggregate yaw recovery above 1 because its mean absolute yaw
  change was lower than control, but this must not be interpreted as biological
  over-recovery.
- Body-height mean and minimum moved back toward control for motor-only and
  combined partial restoration, but not for coordination-only partial
  restoration.
- Body-height range recovery fractions were unstable and denominator-sensitive,
  with mixed per-seed direction/no-farther counts.
- Joint-angle action absolute mean followed the motor scaling as expected:
  motor-only and combined partial restoration were near 0.9231, while
  coordination-only remained near the impaired value.
- Adhesion summaries were present for all conditions and seeds. Mean adhesion
  duty was essentially unchanged across conditions, and transition counts
  remained in the observed 23-25 range.

Recovery fractions are computational quantities only and must not be described
as biological recovery percentages. E5 is not biological rescue, Parkinson's
disease rescue, L-DOPA simulation, dopamine restoration, neuron restoration,
pharmacological treatment, cure, or mechanistic validation.

## Milestone E6 Reproduction Status

Milestone E6 is FROZEN - REPRODUCIBLE EVIDENCE SYNTHESIS. The implementation
commit is `53e41d17365f56509ca708ba3352ddf724b0e89a`.

It consumes exactly eight frozen reports without modifying them or rerunning
simulations:

- `results/baseline/healthy_baseline.json`
- `results/perturbations/identity.json`
- `results/perturbations/action_scale_080.json`
- `results/sweeps/milestone_e1.json`
- `results/sweeps/milestone_e2_combined.json`
- `results/validation/milestone_e3_candidate_robustness.json`
- `results/validation/milestone_e4_concordance.json`
- `results/validation/milestone_e5_computational_rescue.json`

The canonical CPU-only command is:

```bash
python scripts/run_evidence_synthesis.py \
  --config configs/analysis/milestone_e6.yaml \
  --output results/analysis/milestone_e6_synthesis.json
```

The frozen report `results/analysis/milestone_e6_synthesis.json` records
`synthesis_git_commit = 53e41d17365f56509ca708ba3352ddf724b0e89a`, exactly 56
passing checks, input SHA-256 hashes, and upstream git commits. It generated
four figures under `results/analysis/figures/` and five CSV tables under
`results/analysis/tables/`.

The report records `synthesis_worktree_dirty = true`. At synthesis time this
was caused solely by the pre-existing out-of-scope
`notebooks/session_02_healthy_baseline/Session_02_Healthy_Baseline.ipynb` file;
the notebook was not modified, staged, reverted, cleaned, or used as an E6
input. This provenance flag was preserved rather than falsified.

E6 PASS means only that the required computational evidence was internally
consistent and the synthesis artifacts were generated successfully. E4 remains
`PARTIAL_PHENOTYPE_CONCORDANCE`, and E5 remains computational reversibility
only. E6 is not Parkinson's disease validation, biological rescue, mechanistic
validation, disease-severity calibration, or statistical significance.

## Milestone F Final Submission Package

Milestone F is FROZEN - FINAL SUBMISSION PACKAGE. The canonical manuscript
source is `docs/report/final_report.md` at commit
`004488cf7fd5e980137a209d360b977716865e1a`. The committed build implementation
is at commit `82746cf1276d3edf7e8ce3206d83f49b3470e1dd`.

The canonical build command is:

```bash
python scripts/build_final_report.py
```

The final submission artifacts are:

- `dist/Drosophila_PD_FlyGym_Final_Report.docx`
- `dist/Drosophila_PD_FlyGym_Final_Report.pdf`
- `dist/final_report_manifest.json`

The manifest records the manuscript source and build commits, artifact sizes,
SHA-256 hashes, PDF page count, build timestamp, validation/test results, and
scientific scope. The package contains the four frozen E6 figures, manuscript
tables, references, appendices, captions, and reproducibility/provenance
statements without rerunning simulations or changing frozen evidence.

Milestone F is a document-packaging checkpoint only. The scientific boundary
remains a computational/phenomenological model; `PARTIAL_PHENOTYPE_CONCORDANCE`
is qualitative. The package does not claim Parkinson's disease validation,
biological rescue, dopamine equivalence, disease-severity mapping, mechanistic
equivalence, or statistical significance.

## Workflow

GitHub is the source of truth. Google Colab is an execution environment.

Project flow:

1. Codex local work on code, tests, and documentation
2. GitHub version control
3. Google Colab execution
4. FlyGym and MuJoCo simulation runs
5. Logs, metrics, and experiment artifacts
6. GitHub or external artifact storage for reproducible outputs

Codex is a coding agent, not the scientific decision-maker. Scientific
interpretation and stage transitions require explicit project-owner approval.

## Reproducibility Requirements

Every experiment should eventually record:

- Experiment ID
- Git commit
- Python version
- FlyGym version
- MuJoCo version
- Environment details
- Random seed, if applicable
- Duration
- Timestep
- Controller parameters
- Actuator parameters
- Perturbation parameters
- Leg or group affected
- Output metrics
- Output files
- Failure or error logs

Small metadata and metrics files may be version-controlled. Large raw artifacts
should stay out of Git unless explicitly curated.

## Future Stages

The planned high-level stages are:

1. Unperturbed baseline (Milestone C, frozen)
2. Controller interface
3. Controlled perturbations (Milestone D, frozen)
4. Parameter-response characterization (Milestones E1 and E2, frozen)
5. Multi-seed robustness validation (Milestone E3, frozen)
6. Literature-grounded phenotype concordance (Milestone E4)
7. Preregistered computational reversibility (Milestone E5, frozen)
8. Reproducible evidence synthesis (Milestone E6, frozen)
9. Gait metrics
10. PD-like perturbation
11. Healthy vs PD-like comparison
12. Potential biological-rescue interpretation, only after external evidence
   and explicit authorization

No disease-specific modeling should be introduced until the locomotor simulation
infrastructure is stable and the project owner authorizes that stage.

## Research Repository Migration (V3 Preparation)

The repository migration is a documentation and developer-experience program.
It does not add a scientific algorithm, simulation, rollout, perturbation,
dashboard, manager, or validation claim. The additive migration records the
current architecture in `docs/repository_architecture.md`, the intended reuse
surface in `docs/public_api.md`, repository health in `docs/project_health.md`,
and reproducibility policies under `reproducibility/`.

Research directory anchors under `research/` and reusable document templates
under `templates/` are organizational only. Existing scientific files are not
moved for compatibility. The frozen evidence chain, manuscript, report
artifacts, notebooks, and release metadata remain authoritative.

## V4 Real Scientific Campaign Preparation

V4 is a documentation-only preparation package. It defines dataset contracts for
Healthy, PD-reserved computational, Candidate, Control, Validation, and
Benchmark inputs; pre-execution experiment protocols; import-to-publication
analysis playbooks; publication checklists; SOPs; QA gates; and readiness/audit
reports under `docs/v4/`.

V4 does not create datasets, run simulations, add managers/dashboards/plugins or
Digital Twin/workflow modules, alter FlyGym, modify evidence, or introduce a
scientific conclusion. The `pd` dataset label is reserved for a future
computational condition and is not biological Parkinson's disease validation.

## V5 Experimental Campaign 01 - Healthy Baseline

V5 is a planning-only package under `research/campaigns/healthy_baseline/` for
100 future unperturbed computational baseline experiments (`Healthy_001` to
`Healthy_100`, seeds 0-99). It contains schemas, templates, a campaign plan,
execution sequence, publication planning, and reviewer gates.

No V5 rollout, dataset, figure, table, or scientific conclusion has been
created. Execution requires explicit authorization, a new output path, and the
existing documented Healthy baseline pipeline. The Healthy baseline remains a
computational simulation baseline, not biological validation.

## V6 Experimental Campaign Execution Framework

V6 adds an execution-only `drosophila_pd.research_execution` package and
`scripts/run_campaign.py`. The runtime discovers manifest, metadata, and
checksum files under `datasets/` and `research/` without parsing
rollout arrays. Planning templates and missing payloads remain outside the
execution path.

The explicit state machine is `WAITING_DATASET`, `READY`, `RUNNING`,
`VALIDATING`, `EXPORTING`, `COMPLETED`, `FAILED`, and `CANCELLED`. In the
current repository the canonical command returns `WAITING_DATASET` because no
executable dataset payload exists. It does not create rollouts, simulate,
modify FlyGym, or fabricate execution results.

When a real approved dataset is available, V6 delegates to the existing
`StudyOrchestrator` and registers its reports, validation, publication, and
bundle artifacts. V6 does not duplicate or alter Analysis, Statistics,
Computational PD, Scientific Validation, Campaign, Digital Twin, or manuscript
logic. Its outputs are operational execution reports, not new scientific
evidence or biological validation.

## V7 Real FlyGym Dataset Integration

V7 adds the read-only `drosophila_pd.dataset_adapter` package and
`scripts/dataset_cli.py`. The adapter discovers the V4 dataset categories
`healthy`, `pd`, `candidate`, `control`, `validation`, and `benchmark` under
`datasets/` and `research/datasets/`.

It reads manifests, metadata, declared rollout files, SHA-256 values, byte
sizes, supported trajectory formats, and frame counts. It does not run FlyGym
or MuJoCo, generate rollout data, mutate datasets, calculate scientific
metrics, or alter the Analysis, Statistics, Computational-PD, Validation,
Digital Twin, Campaign, or StudyOrchestrator implementations.

The current repository contains no real rollout payload. Live discovery and
validation therefore report `WAITING_DATASET` with all six dataset categories
missing. When an approved manifest-backed dataset is added, the adapter can
report `READY`; the existing V6 runtime remains the execution gate and the
existing `StudyOrchestrator` remains the downstream integration point.

Dataset validation is an integrity check only. It does not establish biological
validity, Parkinson's disease validation, mechanistic equivalence, or any new
scientific conclusion.

## V8 Scientific Experiment Runtime

V8 adds the orchestration-only `drosophila_pd.experiment_runtime` package and
`scripts/experiment_runtime.py`. It binds the V7 dataset adapter result to an
`ExperimentSession`, existing campaign metadata, and the existing
`StudyOrchestrator` without parsing rollout data a second time.

The runtime emits persisted lifecycle events including `DATASET_READY`,
`SESSION_CREATED`, `PIPELINE_STARTED`, `PIPELINE_COMPLETED`,
`VALIDATION_COMPLETED`, `PACKAGE_CREATED`, `FAILED`, and `WAITING_DATASET`.
It writes session, execution, state, artifact, manifest, and summary files
under the operational experiment output directory.

Because this repository has no real rollout dataset, V8 currently stops at
`WAITING_DATASET` and does not call the study pipeline. A ready dataset will
use the existing `StudyOrchestrator`; V8 adds no analysis, statistics,
validation, Digital Twin, dashboard, simulation, or biological interpretation.

## V9 Scientific Operating System

V9 adds the orchestration-only `drosophila_pd.research_kernel` package and
`scripts/kernel.py`. The kernel coordinates the existing V7 Dataset Adapter,
V8 Experiment Runtime, Campaign API, and Study API through a Research Bus,
Service Registry, Resource Manager, and dependency-aware Task Scheduler.

The kernel persists `kernel.log`, `events.json`, `timeline.json`,
`kernel_state.json`, `resources.json`, and `registry.json` under its operational
output directory. Its task graph is `prepare -> bind -> run -> validate ->
package -> archive`; downstream tasks are not marked complete when the V7/V8
dataset gate returns `WAITING_DATASET`.

The current repository has no approved rollout dataset, so V9 boot currently
stops at `WAITING_DATASET`. Existing Digital Twin, Analysis, Statistics,
Computational PD, Validation, and Publication services are recorded as
unavailable bindings until their existing public APIs are explicitly connected.
V9 adds no scientific algorithm, simulation, rollout, biological interpretation,
or new evidence.

## Project A - Healthy Baseline Scientific Study Preparation

Project A is a planning-only preparation package for 100 future Healthy
baseline experiments, `Healthy_001` through `Healthy_100`, with deterministic
seeds 0 through 99. The existing V5 campaign matrix remains the authoritative
experiment specification. Project A adds a Healthy dataset contract, metrics
catalog, Figure 1-8 and Table 1-6 specifications, a publication skeleton, and
reviewer/reproducibility inventories under `research/campaigns/healthy_baseline/`,
`paper/healthy_baseline/`, and `docs/v10/`.

No rollout, dataset, result, figure, table, or scientific conclusion is created
by Project A. When approved real data is placed under `datasets/healthy/`, the
existing V7 dataset adapter, V8 runtime, and V9 kernel remain the integration
path. Their integrity checks and `WAITING_DATASET` gate do not establish
biological validation. Project A does not modify scientific modules, FlyGym,
simulation code, frozen evidence, notebooks, manuscript content, or release
artifacts.

## Project B - Parkinson Study Preparation

Project B is planning-only preparation for 100 future computational-condition
experiments, `PD_001` through `PD_100`, with deterministic seeds 0 through 99.
It adds the study protocol, campaign matrix, separate `pd` manifest contract,
metrics and validation specifications, expected-output and artifact
inventories, reviewer/reproducibility checklists, paper skeleton, and
`docs/v10/Project_B/` operational guidance.

No approved PD configuration, rollout, simulation, synthetic data, new
algorithm, or scientific conclusion is present. The `pd` label is a
computational planning category, not biological Parkinson's disease
validation. The existing V7 adapter and V6/V8/V9 orchestration remain the
execution path, and absence of an approved dataset must remain
`WAITING_DATASET`.

## Project X - Real Dataset Acquisition Pipeline

Project X adds the additive `drosophila_pd.dataset_registry` package. It owns
caller-authorized intake and management of real dataset files only: typed
manifest/version/checksum/metadata models, source scanning, directory/ZIP/
single/multiple-rollout import, duplicate and checksum verification, metadata
and payload health checks, searchable indexing, and explicit report artifact
generation.

The registry creates no rollout, runs no FlyGym or MuJoCo simulation, changes no
scientific algorithm, and adds no Parkinson interpretation. Empty or missing
dataset roots remain `WAITING_DATASET`; invalid packages are `FAILED`. A
`READY` health result means software/data integrity only, not biological
validation.

## Project Y - Large-scale Experiment Campaign Manager

Project Y adds the additive `drosophila_pd.campaign` package for managing
large-scale research campaign plans. It provides declarative experiment
matrices, explicit campaign states, deterministic scheduler queueing, progress
and artifact accounting, provenance/history, dashboard files, and publication
planning assets. Ten execution-disabled templates live under
`configs/campaign_templates/`.

Project Y does not run FlyGym or MuJoCo, create rollouts or data, change
scientific algorithms, or introduce a Parkinson interpretation. Dataset
absence remains `WAITING_DATASET`; planning `READY` is not scientific or
biological validation. Existing `research_campaign` and execution packages are
unchanged for backward compatibility.

## Project Z - Healthy Dataset Execution

Project Z extends the existing `research_execution` runtime and
`scripts/run_campaign.py` for real manifest-backed Healthy rollout execution.
The runtime filters the Healthy dataset path, validates declared payload paths,
checks available checksums, loads canonical JSON/NPZ/trajectory CSV rollouts,
and calls the existing `StudyOrchestrator` once per rollout. The request carries
the imported rollout into the existing analysis, statistics, computational-PD,
scientific-validation, Digital Twin, report, figure, and publication APIs.

Batch execution is sequential and supports `--limit`, persisted per-rollout
resume, and retry control. Each completed rollout is written beneath the
operational output root with the existing analysis/statistics/validation/
reports/figures/publication layout, plus `summary.csv`, `summary.json`, and
`summary.md`. No FlyGym/MuJoCo simulation is started and no rollout is created.

Dataset discovery returns `WAITING_DATASET` when no executable manifest or
payload is available and `INVALID_DATASET` for malformed, unsafe, unsupported,
or checksum-mismatched manifest entries. A completed execution with no
declared reference rollout records scientific validation as `NOT_AVAILABLE`;
it never upgrades that condition to a validation pass or biological claim.
