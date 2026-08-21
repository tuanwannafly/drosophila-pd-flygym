# Behavioral Platform API

## Rollout Input

Use `RolloutData` to wrap arrays:

```python
from drosophila_pd.behavior_platform import RolloutData

rollout = RolloutData(
    condition_id="Healthy",
    sample_id="seed0",
    timestep_s=0.0001,
    thorax_positions=thorax_positions,
    thorax_quaternions=thorax_quaternions,
    com_positions=com_positions,
    joint_positions=joint_positions,
    adhesion_outputs=adhesion_outputs,
)
```

Required arrays:

- `thorax_positions`: shape `(n_samples, 3)`, millimeters.
- `thorax_quaternions`: shape `(n_samples, 4)`, scalar-first quaternion
  convention.
- `timestep_s`: positive finite sampling interval.

Optional arrays:

- `com_positions`: shape `(n_samples, 3)`.
- `joint_positions`: mapping from joint name to per-sample arrays.
- `adhesion_outputs`: mapping from leg or actuator name to per-sample command
  arrays.
- `frames`: optional externally rendered image frames.

## Measurement

```python
from drosophila_pd.behavior_platform import measure_rollout_behavior

measurements = measure_rollout_behavior(rollout)
```

Measured outputs include:

- walking bouts
- pause bouts
- freezing episodes
- walking duty cycle
- instantaneous speed
- heading and yaw
- yaw rate
- turn bouts
- cumulative turning
- left/right bias
- trajectory
- curvature
- tortuosity
- exploration metrics
- COM, joint, and adhesion summaries when arrays are available

## Export

```python
from drosophila_pd.behavior_platform import ExportRequest, export_rollout_package

result = export_rollout_package(
    rollout,
    ExportRequest(output_dir="results/v2/example"),
)
```

Supported export formats:

- CSV: `trajectory.csv`
- JSON: `behavioral_measurements.json`
- NPZ: `rollout_arrays.npz`
- PNG: `rollout_summary.png`

## Visualization And Rendering

`build_viewer_plan()` returns deterministic viewer metadata for an interactive
MuJoCo-capable runtime. `render_offline()` creates deterministic trajectory
frames and supports PNG sequence output directly. GIF and MP4 encoding are
attempted when an `imageio` backend is available; otherwise the PNG sequence is
retained as the fallback artifact.

## Comparison

```python
from drosophila_pd.behavior_platform import ComparisonCondition, compare_rollouts

report = compare_rollouts(
    [
        ComparisonCondition("Healthy", healthy_rollout),
        ComparisonCondition("Candidate", candidate_rollout),
        ComparisonCondition("Rescue", rescue_rollout),
    ]
)
```

The comparison report keeps timelines synchronized and computes deltas from
the first condition. Role labels are caller-supplied computational labels, not
biological validation claims.
