# Performance Report

`BenchmarkSuite` supports the requested categories:

`Import`, `Workspace`, `Plugin`, `Analysis`, `Statistics`, `Comparison`,
`Export`, and `Verification`.

Each category must be registered with a caller-supplied callable. The release
report generator intentionally marks these stages `not_run`; it does not
invent timings and does not execute simulations. `TimingTrace` and
`PerformanceTrace` provide opt-in elapsed-time and memory diagnostics for a
real developer workflow.
