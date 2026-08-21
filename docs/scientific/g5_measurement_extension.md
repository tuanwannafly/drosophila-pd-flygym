# G5 Measurement Extension

G5 adds analysis-only measurements for locomotion rollouts already produced by
the canonical pipeline. It does not change FlyGym setup, controllers,
perturbation logic, frozen evidence, release artifacts, or notebooks.

## Modules

- `drosophila_pd.metrics.trajectory` computes per-sample x/y/z position,
  instantaneous speed, heading, and cumulative distance, and can export a
  trajectory CSV.
- `drosophila_pd.metrics.bouts` segments step speeds into walking and pause
  bouts, reporting bout count, pause count, durations, and walking duty cycle.
- `drosophila_pd.metrics.turning` computes yaw rate, turn-angle summaries,
  turn bouts, cumulative turning, and left/right asymmetry.
- `drosophila_pd.metrics.open_field` computes optional virtual open-field
  occupancy metrics when an arena geometry is declared.
- `drosophila_pd.metrics.measurement_extension` combines these analyses under
  one configuration.

## Inputs

The extension expects arrays already collected by the existing locomotion
pipeline:

- `thorax_positions`, shape `(n_samples, 3)`;
- `thorax_quaternions`, shape `(n_samples, 4)`;
- `timestep_s`.

The position and quaternion arrays follow the same sample convention as the
frozen locomotion metrics: one initial sample plus one sample after each action.

## Metrics

Walking-bout metrics:

- walking bouts and pause bouts,
- bout and pause duration,
- bout and pause count,
- walking duty cycle.

Turning metrics:

- yaw rate,
- turn angle distribution,
- turn bouts,
- cumulative turning,
- left/right asymmetry.

Trajectory metrics:

- trajectory CSV export,
- x/y path,
- instantaneous speed,
- instantaneous heading,
- cumulative distance.

Optional open-field metrics:

- center occupancy,
- border occupancy,
- radial distance,
- exploration index.

Open-field metrics are computed only against a declared virtual arena. They do
not imply the original `FlatGroundWorld` had walls or an experimental open-field
apparatus.

## Scientific Boundary

These measurements are computational observables only. They do not designate a
Parkinson's disease condition, dopamine level, neuron-loss percentage,
biological severity, biological rescue, mechanistic equivalence, or statistical
significance. Any future biological mapping must use explicit external evidence
and must preserve the frozen E4 status unless a new authorized milestone
supersedes it.
