# Analysis Pipeline Architecture

Milestone 7 is a backend post-processing pipeline over normalized rollouts. It does not own simulation, FlyGym, evidence, viewer, or UI state.

The pipeline stages are:

`rollouts -> feature graph -> quality checks -> normalization -> outliers -> batch reports -> comparison matrices -> cache/report`

`AnalysisPipeline` orchestrates the stages. `FeatureGraph` evaluates dependencies lazily and detects cycles. `AnalysisCache` keeps feature, metric, and comparison caches bounded. Each result carries computational scope metadata.
