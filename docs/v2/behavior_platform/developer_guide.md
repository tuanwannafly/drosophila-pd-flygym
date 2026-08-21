# Developer Guide

## Design Rules

- Keep v2 behavioral analysis additive to frozen v1.
- Operate on arrays, not live FlyGym or MuJoCo simulation objects.
- Do not introduce perturbations or tune candidate parameters in the platform.
- Keep biological interpretation outside the measurement layer.
- Store deterministic metadata with every export or comparison.

## Extension Points

Add new measurements by extending `measure_rollout_behavior()` or by adding a
small helper that consumes `RolloutData`. A metric should declare:

- required arrays
- units
- threshold configuration
- deterministic behavior
- unsupported or missing-output behavior

Add new visualizations by creating functions that consume `RolloutData` and a
measurement dictionary. Rendering functions should write files under an
explicit output directory and should not depend on simulation state.

## Error Handling

The platform validates array shape, sample count, finite numeric values, and
positive timesteps. Optional backends for GIF or MP4 encoding may be missing;
in that case `render_offline()` retains deterministic PNG frames and records a
note.

## Testing

Tests use synthetic arrays and must not execute FlyGym, MuJoCo, notebooks, or
simulations. New tests should cover:

- metric values
- edge cases
- export files
- viewer/rendering metadata
- comparison synchronization
- scientific-boundary metadata
