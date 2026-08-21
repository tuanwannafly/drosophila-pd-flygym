# Locomotion Gait Platform Developer Guide

## Design Rules

- Keep the subsystem pure post-processing.
- Accept arrays and metadata, not FlyGym or MuJoCo objects.
- Do not introduce perturbations or controller changes.
- Keep outputs JSON-friendly and deterministic.
- Separate implemented measurements from scientific interpretation.

## Extending Metrics

Add new metrics in `gait.py` when they can be computed from contact, foot, or
joint arrays. Prefer small helpers that return plain dictionaries, lists,
strings, numbers, and booleans.

## Extending Figures

Add static figures to `gait_visualization.py`. Each plotting function should
accept `GaitInput`, an optional precomputed analysis report, and an output path
ending in `.png` or `.svg`.

## Export Compatibility

`export_gait_package()` is the canonical bundle writer. New tabular outputs
should be added as CSV files with stable headers. Large raw arrays should remain
in NPZ outputs rather than JSON.

## Testing

Unit tests should use synthetic arrays and must not execute FlyGym, MuJoCo, or
notebooks. Encoder-dependent animation paths should be tested by monkeypatching
the internal encoder function.
