# Healthy Dataset Contract

Status: planning-only. This contract describes the package that will be
accepted when approved Healthy rollout data is supplied. It does not create,
execute, or validate a scientific rollout.

## Scope

The Healthy package is an **unperturbed computational baseline**. It is not
evidence from real Drosophila, biological validation, a Parkinson's disease
model, or a disease-severity scale.

## Package layout

The dataset root is `datasets/healthy/<semantic-version>/`:

```text
datasets/healthy/<version>/
  manifest.json
  checksum.json
  metadata/
  experiments/
    Healthy_001/
      rollout/
      measurements/
      analysis/
      statistics/
      validation/
      reports/
      metadata/
```

The manifest is authoritative for declared files. An experiment may contain
additional optional outputs only when they are declared and checksummed.
Existing V4 contracts remain the schema source:
`docs/v4/datasets/manifest_schema.yaml`,
`docs/v4/datasets/metadata_schema.yaml`, and the Healthy specializations under
`docs/v4/datasets/healthy/`.

## Required contract fields

`manifest.json` must provide the fields required by the existing manifest
schema: dataset ID, dataset type `healthy`, semantic version, full source
commit, ISO creation time, entries, checksums, license, and citation. The
planning template is `dataset_manifest.template.json`.

Each experiment metadata record must identify the subject/trial or approved
computational equivalent, condition, source, commit, configuration, seed,
environment, duration, timestep, observables, and limitations. The existing
`metadata.template.yaml` is the starting template.

At least one declared rollout trajectory is required for an executable
experiment. The adapter accepts only declared supported trajectory formats;
the file path and format must be recorded in the manifest rather than inferred
from an untracked file. Derived measurements, analysis, statistics, validation,
and reports are optional until generated, but must be declared when present.

`checksum.json` must record SHA-256 and byte size for every payload covered by
the package. A missing, duplicate, unreadable, or mismatched file is an
integrity failure; the adapter must not repair the dataset.

## Version, naming, and provenance

- Dataset versions use semantic versioning; incompatible schema changes require
  a new major version.
- Experiment identifiers are `Healthy_001` through `Healthy_100` and are
  case-sensitive.
- Seeds and configuration are taken from `experiment_matrix.csv`.
- A completed package records the execution commit and environment actually
  used; placeholders from planning templates are not valid execution
  provenance.
- Citation and license metadata must point to repository metadata already
  approved for the release.

## Integrity report

Before execution can proceed, V7 discovery and validation must report a ready
dataset, valid manifest and metadata, declared trajectory files, matching
checksums, valid frame counts, and no missing or duplicate required files.
V6/V7/V8/V9 may then orchestrate the existing pipeline. These checks establish
software/data integrity only; they do not establish biological validity.

No Healthy rollout is present in this planning package.
