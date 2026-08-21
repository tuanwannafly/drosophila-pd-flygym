# Developer Guide

## Rules

- Keep Session07/08 code additive.
- Accept arrays, reports, and JSON configuration.
- Do not run FlyGym or MuJoCo from these modules.
- Do not introduce new perturbations.
- Preserve v1 evidence, notebooks, manuscript, and release artifacts.
- Keep scientific claims out of analysis code.

## Extending Arenas

Add new arena or ROI behavior in `open_field.py` by extending zone masks. Keep
the serialized `Arena` and `ArenaZone` data classes stable.

## Extending Progression

Progression stages should store computational parameters only. Non-numeric
parameters are carried through interpolation by nearest-side selection.

## Extending Dashboards

Dashboard exports should remain deterministic and support static formats. HTML
exports are lightweight specifications, not a live web application server.

## Testing

Tests should use synthetic arrays and monkeypatched encoders for optional video
backends.
