# H1 Behavioral Assay Framework

H1 adds a reusable analysis layer for behavioral assays computed from existing
rollout outputs. It does not run FlyGym or MuJoCo, modify controllers, add
perturbations, change frozen evidence, or reinterpret the frozen computational
candidate.

## Architecture

The package `drosophila_pd.assays` defines a common interface:

- `RolloutAssayInput`: arrays and metadata from an existing rollout;
- `BehavioralAssay`: assay classes expose `specification()` and `evaluate()`;
- `AssayResult`: structured metrics plus implemented/planned metric metadata;
- `run_behavioral_assay_suite()`: evaluates enabled assays from one rollout.

Assays reuse the G5 metric modules where possible:

- `drosophila_pd.metrics.trajectory`;
- `drosophila_pd.metrics.bouts`;
- `drosophila_pd.metrics.turning`;
- `drosophila_pd.metrics.open_field`.

Default analysis settings are recorded in
`configs/analysis/h1_behavioral_assays.yaml`.

## Implemented Assays

### Open Field

Implemented computational metrics:

- trajectory visualization support through plot-ready x/y path arrays;
- center occupancy;
- border occupancy;
- exploration index;
- radial-distance statistics.

Open-field results require declared virtual arena geometry. FlatGroundWorld
trajectories are not automatically equivalent to biological open-field assays.

### Freezing

Implemented computational metrics:

- pause duration;
- pause frequency;
- immobility ratio;
- freezing episode detection from speed-thresholded pause bouts.

These are computational immobility episodes, not validated freezing biology.

### Turning

Implemented computational metrics:

- yaw-rate distribution;
- turn-bout detection;
- cumulative turning;
- left/right bias;
- turn-angle histogram.

Turning is derived from thorax orientation time series. It remains a simulation
observable unless mapped to external evidence in a later validation step.

### Gait

Implemented now:

- adhesion duty factor by leg;
- adhesion transition count by leg.

Planned metrics awaiting additional rollout outputs:

- stance/swing phase by leg;
- stride length and frequency;
- inter-leg coordination phase;
- tripod gait regularity.

Adhesion command summaries are not footfall contact, stance/swing, or validated
gait-phase metrics.

## Scientific Boundary

H1 provides computational behavioral assays only. It does not establish
Parkinson diagnosis, biological validation, disease severity, dopamine
equivalence, rescue, or mechanistic claims.
