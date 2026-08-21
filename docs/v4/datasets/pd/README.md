# PD Dataset Specification

## Purpose

Reserve a controlled intake contract for a future computational PD-like
condition. The repository currently contains no validated biological PD
dataset, and this specification does not create one.

## Contract

- Manifest: `../manifest_schema.yaml`, with `dataset_type: pd`.
- Metadata: `../metadata_schema.yaml`.
- Required provenance: explicit computational definition, source commit,
  configuration, seed, environment, and limitation statement.

## Folder layout

```text
pd/<dataset-version>/
  manifest.json
  metadata/
  rollouts/
  measurements/
  validation/
  reports/
```

## Naming/version/checksum/citation

Use `pd_<condition-id>_<seed>_<artifact>.<ext>`, semantic versions, immutable
SHA-256 manifests, and citations for the repository and any external evidence.
The label `pd` must not be described as disease validation, dopamine
equivalence, severity, or mechanism without supporting evidence.
