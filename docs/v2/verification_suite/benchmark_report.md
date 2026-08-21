# Benchmark Report

`VerificationSuite.benchmarkStress()` delegates timing to the existing
`IntegrationWorkflow.benchmark()` method. It reports per-stage samples and
means for:

- import
- feature extraction
- descriptive statistics
- comparison
- export

It also records optional browser heap readings and feature/metric/comparison
cache entries, hits, and misses.

The requested stress sizes are 1, 10, 100, 1,000, 10,000, and 100,000
frames. A size is measured only when the supplied real rollout contains at
least that many frames. No synthetic expansion, simulation, or scientific
extrapolation is performed.
