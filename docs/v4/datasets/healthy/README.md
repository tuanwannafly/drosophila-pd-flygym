# Healthy Dataset Specification

## Purpose

Organize unperturbed computational baseline rollouts and derived measurements.
This is not biological control data.

## Contract

- Manifest: `../manifest_schema.yaml`, with `dataset_type: healthy`.
- Metadata: `../metadata_schema.yaml`.
- Required provenance: source commit, baseline configuration, environment,
  seed, duration, timestep, and output hashes.

## Folder layout

```text
healthy/<dataset-version>/
  manifest.json
  metadata/
  rollouts/
  measurements/
  reports/
```

## Naming/version/checksum/citation

Use `healthy_<condition>_<seed>_<artifact>.<ext>`, semantic dataset versions,
SHA-256 for every file, and the repository `CITATION.cff` plus the relevant
release/report citation. Never overwrite a frozen baseline.
