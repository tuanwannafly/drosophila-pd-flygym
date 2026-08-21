# Manual Checklist

- [ ] Pass one normalized rollout to `AnalysisPipeline.analyzeRollout`.
- [ ] Confirm graph, feature, statistics, segmentation, QC, and outlier fields exist.
- [ ] Run `analyzeBatch` on multiple rollout records.
- [ ] Inspect normalization parameters for global and per-rollout scopes.
- [ ] Trigger and inspect missing/non-finite/range/duplicate/broken-trajectory findings using known test data.
- [ ] Inspect metric, correlation, similarity, and distance matrices.
- [ ] Confirm repeated analysis uses bounded cache entries.
- [ ] Confirm no simulation, FlyGym call, evidence write, or UI mutation occurs.
