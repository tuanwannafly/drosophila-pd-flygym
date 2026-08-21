# Developer Guide

## Rules

- Keep all code additive on `research/v2-behavior-platform`.
- Accept states, arrays, reports, scenarios, and JSON configuration.
- Do not run simulations from these modules.
- Do not introduce biological treatment models.
- Preserve backward compatibility with earlier v2 modules.
- Keep all scientific language conservative.

## Serialization

Every core data class exposes `as_dict()` and uses JSON-friendly structures.
File writers should use deterministic indentation and sorted keys where
practical.

## Replay

Replay functions reconstruct state from recorded timelines or parameter
schedules. They do not infer missing simulation state.

## Visualization

Visualization exports should support PNG, SVG, PDF, and HTML. HTML exports are
portable summaries rather than hosted applications.

## Testing

Tests should use synthetic data and should not execute FlyGym, MuJoCo, or
notebooks.
