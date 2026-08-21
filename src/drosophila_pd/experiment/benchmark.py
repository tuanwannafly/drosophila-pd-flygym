"""Benchmark adapter for caller-supplied experiment pipeline stages."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from drosophila_pd.scientific_validation.benchmark import benchmark_operations, benchmark_scalability


BENCHMARK_OPERATIONS = (
    "Import",
    "Analysis",
    "Statistics",
    "Validation",
    "Visualization",
    "Export",
)


class ExperimentBenchmark:
    """Measure registered software operations; never runs simulation implicitly."""

    def __init__(self) -> None:
        self._operations: dict[str, Callable[[], Any]] = {}

    def register(self, name: str, operation: Callable[[], Any]) -> None:
        if name not in BENCHMARK_OPERATIONS:
            raise ValueError(f"unsupported experiment benchmark operation: {name}")
        if not callable(operation):
            raise TypeError("operation must be callable")
        self._operations[name] = operation

    def run(self, *, repeats: int = 1, cache_metrics: Mapping[str, Any] | None = None) -> dict[str, Any]:
        report = benchmark_operations(self._operations, repeats=repeats, cache_metrics=cache_metrics)
        report["memory_and_cpu_measured"] = True
        report["registered_operations"] = sorted(self._operations)
        return report

    def run_scalability(
        self,
        operations_by_size: Mapping[str, Mapping[str, Callable[[], Any]]],
        *,
        repeats: int = 1,
    ) -> dict[str, Any]:
        return benchmark_scalability(operations_by_size, repeats=repeats)


__all__ = ["BENCHMARK_OPERATIONS", "ExperimentBenchmark"]
