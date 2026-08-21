# Performance Report

`benchmark` measures import, feature extraction, descriptive statistics, comparison and export separately. It reports per-stage samples, means, optional browser heap values, and cache entries/hits/misses.

The current adapter is sequential and memory-resident. The observed architecture is parallel-ready through the existing batch APIs; worker execution and streaming remain future optimizations. No benchmark result is treated as scientific evidence.
