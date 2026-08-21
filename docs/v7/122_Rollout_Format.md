# Rollout Format

The adapter follows the V4 manifest contract:

- `manifest.json` (or YAML equivalent)
- `dataset_id`, `dataset_type`, `dataset_version`
- `source_commit`, `entries`, `checksums`, `citation`, `scientific_scope`
- `entries[].relative_path`, `sha256`, and `byte_size`
- `metadata/` or a declared metadata file
- rollout files in `rollouts/`

Trajectory inspection supports CSV, JSON, NPZ, and NPY arrays. The adapter
counts frames only for validation; it does not compute scientific metrics.
