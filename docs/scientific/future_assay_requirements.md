# Future Assay Requirements

This file records the evidence required before G8 endpoints can be promoted
from analysis capability to supported or partially supported computational
phenotypes.

## Required G7 Evidence Package

The canonical package should be available at:

```text
results/validation/g7_measurement_enabled_evidence_refresh/
```

Required package-level file:

```text
results/validation/g7_measurement_enabled_evidence_refresh/measurement_enabled_evidence.json
```

Required per-rollout files for each frozen seed and condition:

- `raw_rollout_arrays.npz`;
- `trajectory.csv`;
- `heading.csv`;
- `instantaneous_speed.csv`;
- `yaw_rate.csv`;
- `walking_bouts.csv`;
- `pause_bouts.csv`;
- `turn_bouts.csv`;
- `g5_measurements.json`.

The package must preserve the frozen candidate, seeds, duration, controller,
environment, and perturbation definitions. It must not tune parameters or add
new perturbations.

## Endpoint-Specific Requirements

### Walking and Pause Bouts

Required outputs:

- walking and pause bout tables for baseline and candidate;
- fixed speed threshold and minimum-duration metadata;
- paired seed summaries for bout count, bout duration, pause duration, and
  walking duty cycle.

Biological limitation:

- these are computational bout definitions unless matched to an experimental
  adult Drosophila Parkinson assay.

### Turning

Required outputs:

- yaw-rate time series;
- turn-bout tables;
- cumulative turning and net turning summaries;
- left/right turn decomposition.

Biological limitation:

- current literature support maps most closely to angular velocity; turn bouts
  and left/right asymmetry require additional endpoint-specific support.

### Open-Field Exploration

Required outputs:

- trajectory tables;
- explicit virtual arena geometry;
- center and border definitions;
- center occupancy, border occupancy, radial distance, and exploration index.

Biological limitation:

- FlatGroundWorld trajectories are not automatically equivalent to an
  experimental open-field assay.

## Highest-Value Next Step

Copy or regenerate the canonical G7 measurement-enabled evidence package, then
rerun G8 as a read-only evidence interpretation step. Do not modify frozen
simulation parameters, candidate values, or biological claims.
