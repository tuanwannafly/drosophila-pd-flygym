# API

## Open-field Analysis

```python
from drosophila_pd.behavior_platform import Arena, ArenaZone, analyze_open_field

arena = Arena.rectangular(
    size_xy_mm=(100.0, 100.0),
    border_width_mm=10.0,
    center_fraction=0.5,
    zones=(ArenaZone("roi", "circle", radius_mm=5.0),),
)
report = analyze_open_field(rollout, arena, grid_bins=12)
```

## Progression

```python
from drosophila_pd.behavior_platform import progression_from_config, replay_progression

timeline = progression_from_config("configs/v2/progression.json")
replay = replay_progression(timeline, sample_times_s=[0.0, 10.0, 20.0])
```

Stages store computational parameters only.

## Comparison

```python
from drosophila_pd.behavior_platform import compare_behavior_conditions

comparison = compare_behavior_conditions(
    {
        "Healthy": healthy_report,
        "Candidate": candidate_report,
        "Stage1": stage1_report,
    }
)
```

## Dashboards and Playback

```python
from drosophila_pd.behavior_platform import (
    SynchronizedPlaybackRequest,
    export_behavior_dashboard,
    render_synchronized_playback,
)

export_behavior_dashboard(reports, "results/v2/session07/dashboard")
render_synchronized_playback(
    rollouts,
    SynchronizedPlaybackRequest(output_dir="results/v2/session08/playback"),
)
```
