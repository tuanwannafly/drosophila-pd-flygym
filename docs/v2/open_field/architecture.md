# Architecture

The Session07/08 platform adds open-field arena analysis, computational
progression timelines, multi-condition behavior comparison, dashboard exports,
and synchronized playback exports.

## Modules

- `data_model.py`: `BehaviorEpisode`, `BehaviorSequence`, `Arena`,
  `ArenaZone`, `ProgressionStage`, `ProgressionTimeline`,
  `BehaviorComparison`, `BehaviorReport`, and `BehaviorDashboard`.
- `open_field.py`: rectangular and circular arena analysis, zones, heat maps,
  occupancy, entropy, transitions, dwell time, tortuosity, and curvature.
- `progression.py`: JSON-configured computational stages, interpolation,
  timelines, metadata, and reproducible replay.
- `behavior_comparison.py`: trajectory, DTW, Fréchet, occupancy, gait, turning,
  and exploration similarity.
- `dashboard.py`: dashboard specifications, trajectory explorer, occupancy
  views, radar/parallel summaries, and PNG/SVG/PDF/HTML export.
- `video_system.py`: synchronized split-screen or quad-view playback with
  overlays and PNG/GIF/MP4 export.

## Boundary

The platform does not create simulations, perturbations, or biological disease
claims. Inputs are rollout arrays, contact/gait reports, open-field reports, or
computational progression configurations.
