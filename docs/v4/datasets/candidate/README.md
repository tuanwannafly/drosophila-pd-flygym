# Candidate Dataset Specification

## Purpose

Organize the frozen computational candidate and paired rollout outputs without
turning the candidate into a biological disease model.

## Contract

- Manifest: `../manifest_schema.yaml`, with `dataset_type: candidate`.
- Metadata: `../metadata_schema.yaml`.
- Required provenance: frozen candidate parameters, source commit, configuration,
  seeds, environment, and paired-condition identity.

## Folder layout

```text
candidate/<dataset-version>/
  manifest.json
  metadata/
  rollouts/
  measurements/
  comparisons/
  reports/
```

## Naming/version/checksum/citation

Use `candidate_<candidate-id>_<seed>_<artifact>.<ext>`, semantic versions,
SHA-256 for every artifact, and repository/final-report citations. Preserve the
frozen candidate parameters and never tune them during packaging.
