# Control Dataset Specification

## Purpose

Organize identity controls and other explicitly declared computational controls
used for paired comparisons.

## Contract

- Manifest: `../manifest_schema.yaml`, with `dataset_type: control`.
- Metadata: `../metadata_schema.yaml`.
- Required provenance: control definition, paired experiment ID, source commit,
  seed, environment, and equivalence checks where applicable.

## Folder layout

```text
control/<dataset-version>/
  manifest.json
  metadata/
  rollouts/
  comparisons/
  validation/
```

## Naming/version/checksum/citation

Use `control_<control-id>_<seed>_<artifact>.<ext>`, semantic versions, SHA-256
manifests, and citations to the paired computational protocol. A control is a
software comparison condition, not a clinical or biological control group.
