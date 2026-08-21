# Tutorial

This tutorial assumes rollout arrays already exist.

## 1. Define an Arena

```python
from drosophila_pd.behavior_platform import Arena

arena = Arena.circular(radius_mm=50.0, border_width_mm=10.0)
```

## 2. Analyze Open-field Behavior

```python
from drosophila_pd.behavior_platform import analyze_open_field

open_field = analyze_open_field(rollout, arena, grid_bins=16)
```

## 3. Configure Computational Progression

```python
from drosophila_pd.behavior_platform import progression_from_config

timeline = progression_from_config(
    {
        "timeline_id": "example",
        "stages": [
            {"name": "Stage0", "computational_parameters": {"motor_scale": 1.0}},
            {"name": "Stage1", "computational_parameters": {"motor_scale": 0.9}},
        ],
        "stage_times_s": [0.0, 10.0],
    }
)
```

## 4. Compare Conditions

```python
from drosophila_pd.behavior_platform import compare_behavior_conditions

compare_behavior_conditions({"Healthy": baseline, "Stage1": stage1})
```

## 5. Export Views

```python
from drosophila_pd.behavior_platform import export_behavior_dashboard

export_behavior_dashboard({"Healthy": baseline, "Stage1": stage1}, "results/v2/dashboard")
```
