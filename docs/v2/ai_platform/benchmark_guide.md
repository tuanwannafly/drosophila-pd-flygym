# Benchmark Guide

Benchmarks compare computational datasets and reports across roles such as
Healthy, Candidate, Progression, Intervention, and Custom.

```python
cases = [
    BenchmarkCase("healthy", "Healthy", {"speed": 1.0}),
    BenchmarkCase("candidate", "Candidate", {"speed": 0.8}),
]
report = run_behavior_benchmark(cases)
```

Leaderboards are descriptive computational summaries. They do not define
biological validity or disease severity.
