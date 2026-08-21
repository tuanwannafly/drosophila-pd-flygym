# Benchmark Dataset Specification

## Purpose

Organize inputs and outputs for software and analysis performance benchmarks.

## Contract

- Manifest: `../manifest_schema.yaml`, with `dataset_type: benchmark`.
- Metadata: `../metadata_schema.yaml`.
- Required provenance: operation, input size, environment, repetition/seed
  policy, timing method, and memory method where available.

## Folder layout

```text
benchmark/<dataset-version>/
  manifest.json
  metadata/
  inputs/
  measurements/
  reports/
```

## Naming/version/checksum/citation

Use `benchmark_<operation>_<input-size>_<artifact>.<ext>`, semantic versions,
SHA-256 manifests, and citations to the software release and benchmark method.
Benchmark results describe computational performance, not biological effect.
