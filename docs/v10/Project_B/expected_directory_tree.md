# Expected Directory Tree

```text
datasets/pd/<version>/
  manifest.json
  checksum.json
  metadata/
  experiments/
    PD_001/
      rollout/
      measurements/
      analysis/
      statistics/
      validation/
      reports/
      metadata/
```

The tree is a future input/output contract. Project B creates no directories
under `datasets/` and does not create empty result artifacts.
