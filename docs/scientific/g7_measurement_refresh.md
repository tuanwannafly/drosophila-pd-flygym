# G7 Measurement-Enabled Evidence Refresh

G7 creates a new evidence package for the frozen E3 baseline/candidate
conditions while exporting the raw rollout arrays required by G5 analysis.
It must not overwrite frozen E3, E4, E5, E6, manuscript, release, or notebook
artifacts.

## Frozen Inputs

G7 reuses:

- baseline config: `configs/experiments/healthy_baseline.yaml`;
- validation config: `configs/experiments/validation/milestone_e3.yaml`;
- candidate: `motor_scale = 0.8`, `coupling_scale = 0.75`;
- seeds: `[0, 1, 2, 3, 4]`;
- duration: `1.0 s`;
- controller, actuator, world, timestep, and perturbation definitions from the
  frozen repository pipeline.

No parameter tuning, new perturbation, disease reinterpretation, or biological
claim is introduced.

## Output Package

The default output directory is:

```text
results/validation/g7_measurement_enabled_evidence_refresh/
```

Each seed has baseline and candidate rollout directories containing:

- `raw_rollout_arrays.npz`;
- `trajectory.csv`;
- `heading.csv`;
- `instantaneous_speed.csv`;
- `yaw_rate.csv`;
- `walking_bouts.csv`;
- `pause_bouts.csv`;
- `turn_bouts.csv`;
- `g5_measurements.json`.

The package-level report is:

```text
results/validation/g7_measurement_enabled_evidence_refresh/measurement_enabled_evidence.json
```

## Measurements

The report includes the original derived locomotion metrics plus G5 summaries:

- trajectory path length and instantaneous speed summaries;
- walking bout count, pause count, durations, and duty cycle;
- yaw-rate-derived turn bouts, cumulative turning, and left/right asymmetry;
- optional virtual open-field metrics if enabled by config.

## Scientific Boundary

G7 is a computational evidence refresh only. It does not validate Parkinson's
disease biology, dopamine depletion, neuron loss, disease severity,
pharmacological rescue, mechanistic equivalence, or statistical significance.
