# Dataset Discovery

Discovery searches `datasets/` and `research/` for exact manifest filenames. It
reads manifest, metadata, and checksum metadata only. Rollout arrays and other
scientific payload contents are not parsed by this layer.

Planning templates, manifests marked `PLANNING_ONLY` or `PLANNED`, and
manifests with no payload entries are excluded from execution. Declared
payload paths must exist before a dataset is `READY`; otherwise the runtime
returns `WAITING_DATASET` with a reason and warning.

The V5 Healthy Baseline package is intentionally planning-only, so it does not
unlock V6 execution.
