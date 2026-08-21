# V7 Real FlyGym Dataset Integration

V7 provides a read-only adapter for curated FlyGym rollout datasets. It
discovers the six repository dataset categories, resolves manifest entries,
reads metadata, checks checksums, identifies trajectory files, and reports
frame counts.

No simulation, rollout generation, scientific algorithm, or evidence file is
changed. In the current checkout no curated dataset payload is present, so the
adapter reports `WAITING_DATASET`.

Use `python scripts/dataset_cli.py discover` to inspect availability and
`python scripts/dataset_cli.py validate` before connecting a ready dataset to
the existing execution/runtime pipeline.
