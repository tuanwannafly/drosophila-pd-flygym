# Parkinson Analytics Engine Architecture

The analytics engine is a post-processing layer over normalized FlyGym rollouts. `ParkinsonAnalyticsEngine` coordinates feature extraction, segmentation, descriptive statistics, comparison, and optional configurable score calculation. It does not run simulations, modify controllers, mutate evidence, or alter the existing rollout loader.

The primary flow is:

`normalized rollout -> feature bundle -> behavior segments/statistics -> comparison or configured index -> export/visualization`

`FeatureCache` and `StatisticsCache` avoid repeated work. Missing channels remain unavailable in the returned bundle. `Healthy`, `PD`, `Candidate`, and `Control` are computational comparison labels only.
