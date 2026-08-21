# Locomotion Gait Platform API

## Core Analysis

```python
from drosophila_pd.behavior_platform import GaitInput, analyze_gait

gait_input = GaitInput(
    condition_id="unperturbed",
    timestep_s=0.0001,
    contact_states={
        "LF": lf_contact,
        "LM": lm_contact,
        "LH": lh_contact,
        "RF": rf_contact,
        "RM": rm_contact,
        "RH": rh_contact,
    },
    foot_positions=foot_xyz_by_leg,
    joint_trajectories=joint_values,
)
report = analyze_gait(gait_input)
```

## Rollout Bridge

```python
gait_input = GaitInput.from_rollout(rollout, foot_positions=foot_xyz_by_leg)
```

This uses `rollout.adhesion_outputs` as the contact source. The bridge is
post-processing only.

## Configuration

```python
from drosophila_pd.behavior_platform import GaitAnalysisConfig

report = analyze_gait(
    gait_input,
    config=GaitAnalysisConfig(
        contact_threshold=0.5,
        min_contact_duration_s=0.0,
        min_swing_duration_s=0.0,
        min_stride_duration_s=0.0,
    ),
)
```

## Export

```python
from drosophila_pd.behavior_platform import GaitExportRequest, export_gait_package

result = export_gait_package(
    gait_input,
    GaitExportRequest(
        output_dir="results/v2/gait/session05",
        formats=("csv", "json", "npz", "png", "svg"),
    ),
)
```

## Animation

```python
from drosophila_pd.behavior_platform import GaitAnimationRequest, render_gait_animation

render_gait_animation(
    gait_input,
    GaitAnimationRequest(output_dir="results/v2/gait/session06", format="png_sequence"),
)
```

GIF and MP4 export use `imageio` when available and fall back to deterministic
PNG frames if encoding is unavailable.
