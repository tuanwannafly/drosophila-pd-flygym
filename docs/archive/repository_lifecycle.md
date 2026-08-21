# Repository Lifecycle

## Version 1.0.0

Version 1.0.0 is the frozen public release state. It contains the completed
computational framework, frozen evidence chain, final report artifacts,
publication package, journal submission package, and archive documentation.

## Maintenance State

The `main` branch is the canonical release branch. Infrastructure or
documentation-only updates may be made for public dissemination, archival, or
repository maintenance when they do not modify frozen scientific assets.

## Frozen Assets

The following should remain unchanged for v1.0.0:

- scientific implementation under `src/`
- simulation and perturbation entry points under `scripts/`
- experiment configuration under `configs/`
- tests under `tests/`
- notebooks under `notebooks/`
- frozen evidence JSON under `results/`
- manuscript scientific content under `docs/report/`
- release artifacts under `dist/`

## Future Releases

Any new simulation, perturbation, measurement, biological interpretation, or
manuscript revision should be handled as a new versioned release with its own
evidence and provenance.
