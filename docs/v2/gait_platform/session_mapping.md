# Session Mapping

The locomotion gait platform is the canonical implementation target for
Sessions 05-06.

## Session 05

Session 05 should use `GaitInput`, `analyze_gait()`, and
`export_gait_package()` to produce reproducible gait and contact analysis from
existing rollout arrays.

Expected Session 05 focus:

- derive contact state from adhesion or contact arrays
- detect stance, swing, stride, and gait-cycle events
- compute cadence, stride duration, stride frequency, stride length, duty
  factor, gait symmetry, gait entropy, and gait stability
- export JSON, CSV, NPZ, PNG, and SVG artifacts

## Session 06

Session 06 should use visualization and animation APIs to inspect gait and
coordination outputs.

Expected Session 06 focus:

- render footfall diagrams and contact rasters
- render gait timelines, coordination matrices, phase wheels, stride plots,
  joint trajectories, and foot trajectories
- export PNG sequences, GIFs, or MP4s from existing arrays
- compare gait summaries across conditions without changing perturbation logic

## Boundary

Sessions 05-06 are measurement and visualization sessions only. They must not
modify frozen v1 evidence, manuscript content, release artifacts, or scientific
conclusions.
