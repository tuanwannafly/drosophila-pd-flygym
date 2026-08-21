# Healthy Baseline Metrics Catalog

This catalog inventories metrics already exposed by the repository. It is a
planning index, not a request to add metrics or to infer biological meaning.
Metric names below follow existing Python output keys where they are known.

## Locomotion

- `planar_displacement_mm`
- `planar_displacement_vector_mm`
- `planar_path_length_mm`
- `trajectory_efficiency`
- `mean_planar_speed_mm_s`
- `step_count`, `sample_count`, `requested_duration_s`, `executed_duration_s`,
  and `timestep_s`
- `body_height_below_floor`

Source: `src/drosophila_pd/metrics/locomotion.py` and
`src/drosophila_pd/metrics/trajectory.py`.

## Body

- Body-height count, minimum, maximum, mean, initial, and final summaries
- Initial and final thorax position
- Initial and final heading yaw and yaw change
- Finite-observation and finite-derived-metric flags

These are computational rollout observables and are not biological claims.

## Joint

- Joint-angle action count, minimum, maximum, mean, standard deviation, and
  absolute mean where reported
- Controller action finite checks
- Adhesion duty factor by leg and adhesion transition count by leg

Source: the controller-action summary returned by
`compute_locomotion_metrics`.

## COM

No independent COM metric is asserted by the current Healthy planning
contract. A COM endpoint may be planned only when the supplied rollout and its
declared analysis output contain it. It must not be reconstructed from absent
data or treated as present because a figure is planned.

## Trajectory

- `time_s`, `x_mm`, `y_mm`, `z_mm`
- `heading_rad`
- `instantaneous_speed_mm_s`
- `step_speed_mm_s`
- `cumulative_distance_mm`
- Trajectory duration, path length, final position, mean step speed, and maximum
  step speed summaries

Source: `src/drosophila_pd/metrics/trajectory.py`.

## Behavior

- Walking and pause bouts, counts, durations, walking duty cycle
- Yaw-rate series and summary
- Turn-angle distribution, turn bouts, cumulative turning, net turn angle,
  left/right turning totals, and left/right asymmetry
- Optional open-field center occupancy, border occupancy, radial-distance
  summary, exploration index, and availability status

Sources: `metrics/bouts.py`, `metrics/turning.py`,
`metrics/open_field.py`, `metrics/measurement_extension.py`, and the assay
modules under `src/drosophila_pd/assays/`.

## Validation

- Expected versus executed step count
- Finite observations and finite derived metrics
- Body-height floor criterion
- Expected actuated DOFs and adhesion actuators
- Deterministic seed criterion
- Manifest, metadata, trajectory, frame-count, and checksum integrity

These are software and data-quality checks only.

## Statistics

Existing reports and analysis layers can summarize the measured outputs. This
Project A package does not add inferential tests, thresholds, or statistical
claims. Any future statistic must preserve units, denominators, missing values,
seed handling, and provenance.

## Computational PD

No Healthy baseline metric is labeled a Parkinson's disease endpoint. The
existing computational candidate and perturbation reports remain separate,
frozen evidence and are not changed by this planning package.
