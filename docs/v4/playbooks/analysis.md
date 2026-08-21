# Analysis Playbook

1. Load the validated artifact through existing package APIs.
2. Select only observables present in the input.
3. Compute documented metrics with units and finite-value checks.
4. Preserve raw inputs and record analysis configuration/hash.
5. Export machine-readable results plus warnings and limitations.

Use G5/H1/H2 post-processing modules where applicable; do not rerun simulation
as an implicit analysis step.
