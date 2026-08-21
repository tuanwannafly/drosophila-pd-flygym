# Regression Review

- Existing Python scientific modules were not modified.
- Existing web plugin registry behavior remains available.
- `ExperimentWorkspace.plugins` is preserved; `pluginPlatform` is additive.
- Frozen evidence, notebooks, manuscript, and `dist/` artifacts were not
  changed.
- New tooling uses static inspection and caller-supplied operations.
- Static health checks report heuristic findings as `INFO`, not false failures.

Known repository-level skips remain the three FlyGym/MuJoCo Colab integration
tests. They are unchanged from the preceding checkpoint.
