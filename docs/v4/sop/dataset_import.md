# SOP: Dataset Import

1. Confirm the dataset type and version policy.
2. Inspect the manifest and metadata against the V4 schema.
3. Verify relative paths, byte sizes, and SHA-256 values.
4. Check source commit, configuration, environment, seed, and license/citation.
5. Run existing loader/QC checks without modifying source values.
6. Register the import result and all warnings.

An import failure must leave the previous workspace and curated dataset
unchanged.
