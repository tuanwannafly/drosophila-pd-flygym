# Locomotion Gait Platform Architecture

The v2 gait platform is an additive post-processing layer for Sessions 05-06.
It consumes already-produced rollout arrays and does not run FlyGym or MuJoCo,
modify controllers, introduce perturbations, or change frozen v1 artifacts.

## Components

- `gait.py`: canonical gait, contact, and coordination analysis.
- `gait_export.py`: CSV, JSON, NPZ, PNG, and SVG export packages.
- `gait_visualization.py`: footfall, raster, timeline, coordination, phase,
  stride, joint, and foot plots.
- `gait_animation.py`: PNG sequence, GIF, and MP4 contact-timeline animation.

## Data Flow

```text
RolloutData or GaitInput
  -> analyze_gait()
  -> export_gait_package()
  -> render_gait_visualization_set()
  -> render_gait_animation()
```

## Inputs

The canonical input is `GaitInput`, which stores binary or thresholded contact
state by leg. It may also include foot positions and joint trajectories when
those arrays are available. `GaitInput.from_rollout()` can derive contact state
from `RolloutData.adhesion_outputs`.

## Outputs

The analysis report contains:

- stance and swing bouts
- stride events, stride durations, stride frequencies, stride lengths, and gait
  cycles
- duty factors, contact timelines, footfall events, contact rasters, and
  transition matrices
- left/right symmetry, front-middle-hind summaries, tripod/tetrapod scores,
  coordination matrices, phase locking, and cross correlations
- gait transition counts, gait entropy, and support-count stability summaries

## Boundary

All outputs are computational descriptors of simulated rollout arrays. They are
not biological validation, disease diagnosis, dopamine measurements, or
mechanistic Parkinson's disease claims.
