# Validation Dataset Specification

## Purpose

Organize reproducibility, robustness, schema, and endpoint-validation artifacts
derived from existing computational outputs.

## Contract

- Manifest: `../manifest_schema.yaml`, with `dataset_type: validation`.
- Metadata: `../metadata_schema.yaml`.
- Required provenance: validation class, input evidence paths, source commits,
  hashes, checks, and explicit pass semantics.

## Folder layout

```text
validation/<dataset-version>/
  manifest.json
  metadata/
  inputs/
  checks/
  reports/
  figures/
```

## Naming/version/checksum/citation

Use `validation_<scope>_<input-id>_<artifact>.<ext>`, semantic versions, hashes
for inputs and outputs, and citations to the evidence/report being validated.
Validation status must not be upgraded by a packaging step.
