# Sprint 1 benchmark report

`ExperimentBenchmark` wraps the repository's caller-supplied benchmark
primitives. It records CPU time, peak memory, output hashes, cache metadata and
optional size-grouped scalability measurements for registered operations.
Simulation is never discovered or executed implicitly.
