# Performance Report

Feature and statistics caches use bounded maps with configurable limits. Extraction is lazy: a rollout is analyzed only when a feature, statistics, segmentation, comparison, or score request is made. Vector and scalar operations are single-pass or bounded by the source rollout length.

The current browser implementation retains normalized rollout arrays in memory. Streaming chunk readers, workers, and persistent cache storage are future extensions for very large datasets. No automatic simulation or evidence regeneration is performed.
