# Batch and Comparison

`analyzeBatch` accepts multiple rollout or experiment records, returns per-item reports, aggregate quality, a metric difference matrix, correlation matrix, similarity matrix, and distance matrix. The result marks the implementation `parallelReady`; current execution is deterministic sequential JavaScript, leaving worker scheduling as an infrastructure extension.

Matrix condition labels are computational labels only. Difference, correlation, similarity, distance, and ranking are descriptive outputs and are not biological validation tests.
