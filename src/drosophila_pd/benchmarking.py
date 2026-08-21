"""Generic, opt-in benchmark primitives for release engineering."""

from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Callable


BENCHMARK_STAGES = (
    "Import",
    "Workspace",
    "Plugin",
    "Analysis",
    "Statistics",
    "Comparison",
    "Export",
    "Verification",
)


@dataclass
class BenchmarkResult:
    name: str
    iterations: int
    samples_seconds: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def mean_seconds(self) -> float | None:
        return sum(self.samples_seconds) / len(self.samples_seconds) if self.samples_seconds else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "samples_seconds": list(self.samples_seconds),
            "mean_seconds": self.mean_seconds,
            "errors": list(self.errors),
        }


class BenchmarkSuite:
    """Run only caller-supplied operations; it never runs a simulation itself."""

    def __init__(self, *, clock: Callable[[], float] = time.perf_counter) -> None:
        self.clock = clock
        self.operations: dict[str, Callable[[], Any]] = {}

    def register(self, name: str, operation: Callable[[], Any]) -> None:
        if name not in BENCHMARK_STAGES:
            raise ValueError(f"Unknown benchmark stage: {name}")
        if not callable(operation):
            raise TypeError("Benchmark operation must be callable.")
        self.operations[name] = operation

    def run(self, *, iterations: int = 1) -> dict[str, Any]:
        iterations = max(1, int(iterations))
        results = []
        for name, operation in self.operations.items():
            result = BenchmarkResult(name, iterations)
            for _ in range(iterations):
                started = self.clock()
                try:
                    operation()
                    result.samples_seconds.append(self.clock() - started)
                except Exception as error:  # pragma: no cover - caller operation controls this path
                    result.errors.append(f"{type(error).__name__}: {error}")
            results.append(result.as_dict())
        return {
            "stages": results,
            "stage_count": len(results),
            "iterations": iterations,
            "complete": all(not result["errors"] for result in results),
            "scope": "Software timing only; no scientific result is inferred.",
        }
