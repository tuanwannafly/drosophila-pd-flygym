"""Structured, opt-in diagnostics for developer and release workflows."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import time
import tracemalloc
from typing import Any, Callable


class StructuredEventLog:
    """In-memory structured event log with JSON-friendly records."""

    def __init__(self, *, clock: Callable[[], str] | None = None) -> None:
        self._clock = clock or (lambda: datetime.now(timezone.utc).isoformat())
        self.events: list[dict[str, Any]] = []

    def record(self, event: str, *, level: str = "INFO", payload: dict[str, Any] | None = None) -> dict[str, Any]:
        item = {"timestamp": self._clock(), "event": str(event), "level": str(level), "payload": dict(payload or {})}
        self.events.append(item)
        return item

    def clear(self) -> None:
        self.events.clear()

    def as_dict(self) -> dict[str, Any]:
        return {"event_count": len(self.events), "events": [dict(event) for event in self.events]}


class DebugLogger:
    """Small logger facade that writes only to a supplied event sink."""

    def __init__(self, events: StructuredEventLog | None = None, *, enabled: bool = True) -> None:
        self.events = events or StructuredEventLog()
        self.enabled = enabled

    def log(self, level: str, event: str, **payload: Any) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        return self.events.record(event, level=level.upper(), payload=payload)

    def debug(self, event: str, **payload: Any) -> dict[str, Any] | None:
        return self.log("DEBUG", event, **payload)

    def info(self, event: str, **payload: Any) -> dict[str, Any] | None:
        return self.log("INFO", event, **payload)

    def warning(self, event: str, **payload: Any) -> dict[str, Any] | None:
        return self.log("WARNING", event, **payload)

    def error(self, event: str, **payload: Any) -> dict[str, Any] | None:
        return self.log("ERROR", event, **payload)


@dataclass
class TimingTrace:
    """Context manager that records elapsed wall time for one operation."""

    name: str
    events: StructuredEventLog
    clock: Callable[[], float] = time.perf_counter
    _started: float | None = None

    def __enter__(self) -> "TimingTrace":
        self._started = self.clock()
        self.events.record("timing.start", payload={"name": self.name})
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        started = self._started if self._started is not None else self.clock()
        elapsed = self.clock() - started
        self.events.record("timing.stop", level="ERROR" if exc_type else "INFO", payload={"name": self.name, "elapsed_seconds": elapsed, "error": str(exc_value) if exc_value else None})


class PerformanceTrace:
    """Optional memory/timing trace for one named operation."""

    def __init__(self, name: str, events: StructuredEventLog) -> None:
        self.name = name
        self.events = events
        self.started: float | None = None
        self.memory_started: int | None = None

    def start(self) -> "PerformanceTrace":
        self.started = time.perf_counter()
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        self.memory_started = tracemalloc.get_traced_memory()[0]
        return self

    def stop(self, **payload: Any) -> dict[str, Any]:
        started = self.started if self.started is not None else time.perf_counter()
        elapsed = time.perf_counter() - started
        memory_now = tracemalloc.get_traced_memory()[0] if tracemalloc.is_tracing() else None
        result = {
            "name": self.name,
            "elapsed_seconds": elapsed,
            "memory_start_bytes": self.memory_started,
            "memory_end_bytes": memory_now,
            "memory_delta_bytes": memory_now - self.memory_started if memory_now is not None and self.memory_started is not None else None,
            **payload,
        }
        self.events.record("performance.trace", payload=result)
        return result


class DiagnosticReport:
    """Combine event log, health and optional benchmark data."""

    def __init__(self, *, events: StructuredEventLog, health: dict[str, Any] | None = None, benchmark: dict[str, Any] | None = None) -> None:
        self.events = events
        self.health = health or {}
        self.benchmark = benchmark or {}

    def build(self) -> dict[str, Any]:
        return {
            "event_log": self.events.as_dict(),
            "health": dict(self.health),
            "benchmark": dict(self.benchmark),
            "scope": "Developer diagnostics only; no simulation or scientific interpretation is performed.",
        }
