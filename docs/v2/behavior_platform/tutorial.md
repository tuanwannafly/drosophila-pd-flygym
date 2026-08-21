# Tutorial

This tutorial uses existing rollout arrays. It does not run FlyGym or MuJoCo.

## 1. Wrap Rollout Arrays

```python
from drosophila_pd.behavior_platform import RolloutData

rollout = RolloutData(
    condition_id="Healthy",
    timestep_s=0.0001,
    thorax_positions=thorax_positions,
    thorax_quaternions=thorax_quaternions,
    adhesion_outputs=adhesion_outputs,
)
```

## 2. Measure Behavior

```python
from drosophila_pd.behavior_platform import measure_rollout_behavior

measurements = measure_rollout_behavior(
    rollout,
    config={
        "walking": {"speed_threshold_mm_s": 1.0},
        "freezing": {"immobility_speed_threshold_mm_s": 0.5},
        "turning": {"turn_rate_threshold_rad_s": 0.5},
        "open_field": {"enabled": True},
    },
)
```

## 3. Export A Rollout Package

```python
from drosophila_pd.behavior_platform import ExportRequest, export_rollout_package

export_rollout_package(
    rollout,
    ExportRequest(output_dir="results/v2/session03/healthy_seed0"),
)
```

The package contains trajectory CSV, measurement JSON, compressed arrays, and
a static PNG summary.

## 4. Build Viewer Metadata

```python
from drosophila_pd.behavior_platform import build_viewer_plan

viewer_plan = build_viewer_plan(rollout)
```

The plan records camera presets, overlays, timeline settings, and pause/replay
controls. Opening an actual MuJoCo viewer requires an interactive runtime.

## 5. Compare Conditions

```python
from drosophila_pd.behavior_platform import ComparisonCondition, compare_rollouts

report = compare_rollouts(
    [
        ComparisonCondition("Healthy", healthy),
        ComparisonCondition("Candidate", candidate),
        ComparisonCondition("Rescue", rescue),
    ]
)
```

The output is a synchronized computational comparison. It does not classify
any condition as biologically validated disease or rescue.
