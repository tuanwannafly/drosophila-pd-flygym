# Dataset Report

`python scripts/dataset_cli.py report` writes:

- `dataset_report.json`
- `dataset_report.md`

The report records datasets found, missing categories, metadata, rollout file
inventory, frame counts, checksum findings, validation output, and warnings.
With no dataset payload, it records `WAITING_DATASET` and does not fabricate a
report of scientific observations.
