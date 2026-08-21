# Parkinson Study Protocol

## Status and scope

This is a preparation protocol for a future **computational condition study**.
It is not a protocol for diagnosing, validating, or modeling biological
Parkinson's disease. No biological severity, dopamine equivalence, neuron loss,
or mechanistic interpretation is specified.

The study reuses the existing dataset adapter, orchestration, metrics,
analysis, validation, and publication layers. It adds no scientific algorithm
and does not modify FlyGym or simulation code.

## Planned units

The campaign reserves `PD_001` through `PD_100`, with deterministic planning
seeds 0 through 99. Each row remains `PLANNED` until an approved computational
configuration and real rollout package exist.

## Execution gates

1. Discover a manifest-backed dataset under the approved dataset root.
2. Validate manifest, metadata, declared trajectories, frame counts, and
   checksums with the existing V7 adapter.
3. Require `READY`; otherwise stop at `WAITING_DATASET`.
4. Bind the dataset through the existing V6/V8/V9 orchestration path.
5. Run only the existing analysis and validation layers after authorization.
6. Generate reports and publication assets only from completed outputs.

No stage creates a rollout or repairs a dataset. Integrity PASS is software and
data-quality validation, not biological validation.

## Paired-study rule

Any future comparison with the unperturbed baseline must preserve the approved
seed, duration, timestep, world, controller, and unrelated parameters. The
comparison definition must be recorded before execution. Project B does not
select or tune a candidate condition.
