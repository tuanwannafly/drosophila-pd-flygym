# V2 Behavioral Platform

This directory documents the canonical behavioral platform for Version 2 and
Sessions 03-04. The platform is additive to the frozen v1 release. It operates
on rollout arrays and does not change v1 evidence, manuscript content, release
artifacts, perturbation logic, or simulation code.

## Modules

- `drosophila_pd.behavior_platform.rollout`: typed rollout array container.
- `drosophila_pd.behavior_platform.measurement`: complete behavioral
  measurement engine.
- `drosophila_pd.behavior_platform.export`: CSV, JSON, NPZ, and PNG rollout
  package exporters.
- `drosophila_pd.behavior_platform.visualization`: interactive viewer plans,
  camera presets, overlays, and static summary plots.
- `drosophila_pd.behavior_platform.rendering`: offline PNG sequence, GIF, MP4,
  and comparison rendering entry points.
- `drosophila_pd.behavior_platform.comparison`: Healthy/Candidate/Rescue
  comparison summaries and synchronized playback plans.
- `drosophila_pd.behavior_platform.gait`: Session05 gait, contact, and
  coordination analysis.
- `drosophila_pd.behavior_platform.gait_export`: Session05 CSV, JSON, NPZ, PNG,
  and SVG gait package exporters.
- `drosophila_pd.behavior_platform.gait_visualization`: Session06 footfall,
  raster, timeline, coordination, phase, stride, joint, and foot plots.
- `drosophila_pd.behavior_platform.gait_animation`: Session06 PNG sequence,
  GIF, and MP4 gait animation export.

## Scientific Boundary

The platform computes behavioral measurements from already-produced simulation
rollouts. It does not introduce perturbations, tune candidate parameters,
rerun simulations automatically, or make biological Parkinson's disease
claims.
