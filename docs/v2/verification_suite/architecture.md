# Verification Suite Architecture

Milestone 10 adds a verification adapter around the existing web analysis
pipeline. The adapter is `web/verification_suite.js` and composes
`IntegrationWorkflow`; it does not replace or modify the importer, analysis
modules, statistical engine, exporter, or workspace persistence.

The input boundary is an already available FlyGym-compatible rollout object.
The suite never creates rollout frames, invokes FlyGym, or runs a simulation.
It checks the ordered pipeline, invalid-input rollback, deterministic output
projections, and benchmark measurements.

The stress runner measures only sizes that can be obtained by slicing the
caller-supplied rollout. If a requested size is larger than the input, it is
reported as `insufficient-input`, not fabricated or extrapolated.
