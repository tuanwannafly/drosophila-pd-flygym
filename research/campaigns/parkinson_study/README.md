# Project B: Parkinson Study Preparation

Planning-only assets for 100 future computational-condition experiments,
`PD_001` through `PD_100`.

This package does not define a biological Parkinson's disease model, create a
rollout, run a simulation, generate data, or add an algorithm. The `pd` label
is a reserved computational dataset category used for planning and must not be
read as biological validation.

## Package

- `study_protocol.md` - scope and execution gates.
- `campaign.yaml` - campaign metadata and the disabled execution guard.
- `experiment_matrix.csv` - the authoritative 100-row plan.
- `manifest.schema.json` and `dataset_manifest.template.json` - dataset
  contract and empty planning manifest.
- `metadata.template.yaml` and `checksum.template.json` - future metadata and
  integrity templates.
- `dataset_specification.md`, `metrics_specification.md`, and
  `validation_protocol.md` - requirements using existing pipeline outputs.
- `expected_outputs.md` and `artifact_inventory.md` - artifact contracts.
- `reviewer_checklist.md` and `reproducibility_checklist.md` - review gates.

Execution remains blocked until a real approved dataset is discovered by the
existing V7 adapter. The expected operational result is `WAITING_DATASET`.
