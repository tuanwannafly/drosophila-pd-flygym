# API Index

- `IntegrationWorkflow.importRollout(rawData, options)` runs one end-to-end workflow.
- `IntegrationWorkflow.analyzeBatch(items, options)` analyzes multiple raw rollouts and builds comparison matrices.
- `IntegrationWorkflow.benchmark(rawData, options)` measures import, feature, statistics, comparison and export stages.
- `IntegrationWorkflow.persistAndVerify()` checks workspace persistence round-trip.
- `IntegrationWorkflow.restoreSnapshot(snapshot)` restores state after a failed operation.

The adapter reuses existing public modules and does not change their signatures.
