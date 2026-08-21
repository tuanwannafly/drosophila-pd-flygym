"""Opt-in benchmarks for caller-supplied post-processing operations."""

from __future__ import annotations

import time
import tracemalloc
from typing import Any, Callable, Mapping

from .reproducibility import hash_payload


def benchmark_operations(
    operations: Mapping[str, Callable[[], Any]],
    *,
    repeats: int = 3,
    capture_memory: bool = True,
    cache_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Measure supplied operations; does not discover or execute simulations."""

    if int(repeats) <= 0:
        raise ValueError("repeats must be positive")
    results: dict[str, Any] = {}
    for name, operation in operations.items():
        durations = []
        peaks = []
        output_hash = None
        for _ in range(int(repeats)):
            if capture_memory:
                tracemalloc.start()
            start = time.perf_counter()
            output = operation()
            durations.append(time.perf_counter() - start)
            if capture_memory:
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                peaks.append(int(peak))
            output_hash = hash_payload(output)
        results[name] = {
            "repeats": int(repeats),
            "mean_cpu_time_s": sum(durations) / len(durations),
            "min_cpu_time_s": min(durations),
            "max_cpu_time_s": max(durations),
            "peak_memory_bytes": max(peaks) if peaks else None,
            "output_hash": output_hash,
        }
    return {"operations": results, "cache_metrics": dict(cache_metrics or {}), "scope": "Software post-processing benchmark for caller-supplied operations."}


def benchmark_scalability(
    operations_by_size: Mapping[str, Mapping[str, Callable[[], Any]]],
    *,
    repeats: int = 1,
) -> dict[str, Any]:
    """Benchmark named operations grouped by caller-defined input size."""

    return {
        "scales": {size: benchmark_operations(operations, repeats=repeats) for size, operations in operations_by_size.items()},
        "scope": "Scalability benchmark over supplied finite datasets or operations only.",
    }


__all__ = ["benchmark_operations", "benchmark_scalability"]
