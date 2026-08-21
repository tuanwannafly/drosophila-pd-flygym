# Limitations

- The campaign engine does not run FlyGym or MuJoCo by itself.
- CLI execution uses a deterministic infrastructure-validation executor unless
  an external executor is supplied in downstream code.
- Figure generation is generic and depends on the metrics present in result
  mappings.
- Optional Parquet and Arrow export requires the optional `pyarrow` dependency.
- The engine verifies hashes and manifests, not biological validity.
- No disease-specific inference is implemented.
