# Methods

## Scope and provenance

This report describes a staged computational workflow for an in-silico
Drosophila locomotion model. The frozen sequence contains an unperturbed
simulation baseline, explicit computational perturbation proxies, paired
response surfaces, multi-seed robustness, a limited literature comparison, and
computational reversibility. It does not define a biological disease model.

The final synthesis reads exactly eight frozen upstream evidence reports and
records their paths, commits, byte sizes, and SHA-256 hashes. E6 performs
evidence validation and synthesis only; it does not execute a new FlyGym or
MuJoCo simulation.

## Software and simulation environment

The simulation evidence was generated in Google Colab using Python 3.12.13,
FlyGym 2.1.0, and MuJoCo 3.9.0. The repository also records the Colab
requirements in `requirements-colab.txt`. The canonical locomotion pipeline
uses NeuroMechFly with post-materialization joints, the FlyGym
`FlatGroundWorld`, `Simulation`, `PreprogrammedSteps`, and the official
FlyGym CPG controller source used by the frozen baseline.

The Milestone C unperturbed baseline used a 0.5 s simulation, a 0.0001 s time
step, and 5000 steps. It compiled 42 position actuators and 6 adhesion
actuators, for MuJoCo `nu = 48`. Observations and derived metrics were checked
for finiteness.

## Baseline and controlled perturbations

Every condition creates a fresh fly, world, and simulation. The baseline uses
the same world, controller, timing, and adhesion configuration as its paired
conditions. Perturbations are applied through explicit interfaces and are
logged with their configuration and provenance.

The two E1 proxies are deliberately phenomenological:

- `motor_vigor_proxy`: a global scale on joint-angle action commands.
- `coordination_proxy`: a scale on CPG inter-leg coupling weights.

They are not mappings to dopamine depletion, neuron loss, disease stage, or
any other biological quantity. E1 sampled motor scales `[1.0, 0.9, 0.8, 0.7,
0.6]` and coupling scales `[1.0, 0.75, 0.5, 0.25, 0.0]`.

E2 evaluated nine conditions: the control, three motor-only conditions
(`0.8/1.0`, `0.7/1.0`, `0.6/1.0`), two coordination-only conditions
(`1.0/0.75`, `1.0/0.5`), and three combined conditions
(`0.8/0.75`, `0.7/0.75`, `0.7/0.5`). The first number is motor scale and the
second is coupling scale.

## Robustness design

E3 froze the candidate `motor_scale = 0.8`, `coupling_scale = 0.75` without
post-hoc tuning. It ran paired baseline and candidate conditions for seeds
`[0, 1, 2, 3, 4]`, with the same seed within each pair, fresh simulation state
per condition, and a 1.0 s duration. The candidate transformation and all
controlled variables were checked before the response deltas were interpreted.

## Literature comparison

E4 is a directional qualitative comparison to selected adult walking endpoints
from the configured literature layer. It does not create a disease score,
estimate a biological parameter, or establish mechanistic equivalence. The
reported classification is `PARTIAL_PHENOTYPE_CONCORDANCE` because only some
selected speed and distance directions were comparable.

## Reversibility analysis

E5 evaluated computational restoration from the frozen candidate toward the
control along motor, coordination, and combined parameter axes. Its primary
endpoints were mean planar speed and planar path length. Conditions were
paired with fresh simulation state and held unrelated settings constant. A
directionally recovered endpoint means that the simulated value moved toward
the control under the configured computational restoration. It does not mean
biological rescue, treatment response, or reversibility of disease.

## E6 synthesis and derived quantities

E6 validates the eight input reports, their SHA-256 manifest, expected artifact
inventory, frozen candidate definition, milestone statuses, scientific-boundary
phrasing, and absence of statistical-significance claims. It produces four
figures and five CSV tables. Relative changes are reported as the difference
from the corresponding control divided by that control when the source report
defines that quantity. No new thresholds or biological acceptance criteria are
introduced by the report.

## Terminology

The preferred term for the control condition is **unperturbed baseline**.
Existing identifiers such as `healthy_baseline` remain in file names and
schemas for compatibility with the frozen evidence.
