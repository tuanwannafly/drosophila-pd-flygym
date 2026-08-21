# Healthy Baseline Experiment Plan

## Matrix

The matrix contains exactly 100 planned experiments:

- IDs: `Healthy_001` through `Healthy_100`.
- Seeds: integer `0` through `99`, respectively.
- Configuration: `configs/experiments/healthy_baseline.yaml`.
- Status: `PLANNED` for every row.
- Validation profile: `computational_baseline_reproducibility`.
- Publication targets: the Healthy publication asset layout.

The machine-readable source is `experiment_matrix.csv`. It is a plan, not an
experiment result.

## Expected output contract

Each future experiment may produce only after authorization:

```text
healthy_baseline/<experiment-id>/
  rollout/
  measurements/
  analysis/
  statistics/
  validation/
  reports/
  metadata/
  manifest.json
  checksum.json
```

The exact rollout fields and metrics must come from the existing pipeline. No
placeholder observations are accepted.

## Execution sequence

```text
Import -> Campaign -> Analysis -> Statistics -> Validation -> Publication -> Bundle -> Archive
```

## Pass semantics

PASS means the declared computational checks completed, outputs are finite and
traceable, and manifests are internally consistent. It does not mean biological
validation or a disease conclusion.
