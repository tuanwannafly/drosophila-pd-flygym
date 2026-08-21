# Performance Review

Feature and metric evaluation is lazy through `FeatureGraph` and bounded caches. Batch execution reuses per-rollout cache entries. Quality checks walk source arrays once per channel, while comparison matrices operate on compact metric vectors.

The current implementation is memory-resident and sequential. Streaming readers, worker execution, chunk-level eviction, and persistent caches remain future engineering work for very large datasets. No automatic simulation is started by the pipeline.
