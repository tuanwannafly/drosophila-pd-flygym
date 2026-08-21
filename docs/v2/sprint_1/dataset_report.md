# Sprint 1 dataset report

`DatasetManager` creates the requested role directories and metadata manifests
without creating sample data. Existing files can be registered with role,
record identifier, byte size and SHA-256. Verification, deterministic
partitioning and merge-by-copy are available for real completed outputs.

Existing v2 `DatasetExporter` remains the format layer for JSON, CSV, NPZ,
Parquet and Arrow. Sprint 1 manages references and integrity rather than
inventing new scientific serialization.
