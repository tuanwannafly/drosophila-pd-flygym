# Dataset Specification

## Contracted layout

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

The manifest is authoritative. It must declare every payload, relative path,
byte size, and SHA-256. Each experiment must have an approved configuration,
seed, environment, timing, and a declared trajectory before it can be ready.

## Requirements

- `dataset_type` is `pd` only as a computational planning category.
- Dataset versions are semantic versions.
- Experiment IDs are `PD_001` through `PD_100`.
- Missing, duplicate, unreadable, or checksum-mismatched files fail integrity.
- No adapter or runtime repairs data or infers absent observables.
- No dataset status implies biological Parkinson's disease validation.

The existing V7 adapter and V4 manifest conventions are the integration
reference. Project B does not alter those implementations.
