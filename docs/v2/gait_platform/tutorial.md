# Locomotion Gait Platform Tutorial

This tutorial assumes rollout arrays already exist. It does not create or run a
simulation.

## 1. Build Gait Input

Prepare one contact vector per leg with the same sample count.

```python
from drosophila_pd.behavior_platform import GaitInput

gait_input = GaitInput(
    condition_id="example",
    sample_id="seed0",
    timestep_s=0.0001,
    contact_states=contact_by_leg,
    foot_positions=foot_xyz_by_leg,
    joint_trajectories=joint_values,
)
```

## 2. Analyze Gait

```python
from drosophila_pd.behavior_platform import analyze_gait

report = analyze_gait(gait_input)
```

Inspect `report["contact_analysis"]`, `report["gait_analysis"]`, and
`report["coordination_analysis"]`.

## 3. Export Artifacts

```python
from drosophila_pd.behavior_platform import GaitExportRequest, export_gait_package

export_gait_package(
    gait_input,
    GaitExportRequest(
        output_dir="results/v2/gait/example",
        formats=("csv", "json", "npz", "png", "svg"),
    ),
)
```

The package includes contact timeline CSV, stride-event CSV, duty-factor CSV,
the complete JSON report, compressed arrays, and static figures.

## 4. Render Animation

```python
from drosophila_pd.behavior_platform import GaitAnimationRequest, render_gait_animation

render_gait_animation(
    gait_input,
    GaitAnimationRequest(output_dir="results/v2/gait/example_animation", stride=10),
)
```

Use `format="gif"` or `format="mp4"` when the local runtime has an encoder.
