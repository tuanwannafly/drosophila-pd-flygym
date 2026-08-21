# Dataset Guide

`CampaignDatasetBuilder` converts completed campaign result mappings into the
existing `BehaviorDataset` model. It supports JSON, CSV, NPZ, and optional
Parquet or Arrow through the existing dataset exporter.

Each exported dataset package can include:

- dataset file;
- dataset manifest;
- dataset index;
- checksums;
- metadata.

The builder accepts already-completed rollout summaries and arrays. It does not
run simulations and does not alter perturbation logic.

When campaign results contain rollout arrays, those arrays are preserved in the
dataset sample. When only metrics are available, numeric metrics are stored as a
compact `metrics_vector` for infrastructure validation.
