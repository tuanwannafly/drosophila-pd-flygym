# Dataset Guide

`BehaviorDataset` stores `BehaviorSample` records with arrays, labels, metadata,
versioning, and checksums.

Supported formats:

- JSON
- CSV
- NPZ
- Parquet, when `pyarrow` is installed
- Arrow, when `pyarrow` is installed

Use `DatasetManifest` and `verify_dataset_integrity()` to check sample-level
SHA-256 checksums.
