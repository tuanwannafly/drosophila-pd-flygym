# Manual Checklist

- [x] Discover `healthy`, `pd`, `candidate`, `control`, `validation`, and `benchmark` categories.
- [x] Report `WAITING_DATASET` when no manifest-backed dataset exists.
- [x] Validate structural manifest, checksum, metadata, path, and frame-count contracts in tests.
- [x] Confirm the adapter does not run simulation code.
- [ ] Place an approved FlyGym dataset under `datasets/<type>/<version>/`.
- [ ] Run `python scripts/dataset_cli.py validate` on the real dataset.
- [ ] Run the V6 execution command only after validation passes.

The unchecked steps require external curated rollout data and were not
performed in this repository state.
