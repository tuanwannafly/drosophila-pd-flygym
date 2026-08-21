# Performance Benchmark Review

The engine uses array-local computations and a bounded result cache for repeated descriptive requests. Bootstrap and permutation iteration counts are configurable and seeded. `benchmark(values, options)` reports elapsed wall-clock time for a repeatable local smoke benchmark.

Large resampling jobs remain synchronous and memory-resident. Worker execution, streaming resampling, and persistent cache manifests are future extensions.
