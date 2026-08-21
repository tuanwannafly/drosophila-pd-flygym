"""Dependency-aware orchestration scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .kernel_events import KernelEventType, ResearchBus


TaskHandler = Callable[[], Any]


@dataclass(frozen=True)
class TaskSpec:
    name: str
    handler: TaskHandler
    dependencies: tuple[str, ...] = ()


@dataclass
class TaskResult:
    name: str
    status: str
    value: Any = None
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "task": self.name,
            "status": self.status,
            "value": _jsonable(self.value),
            "error": self.error,
            "metadata": _jsonable(self.metadata),
        }


class TaskScheduler:
    """Run registered tasks once, respecting explicit dependencies."""

    def __init__(self, bus: ResearchBus | None = None) -> None:
        self.bus = bus
        self._tasks: dict[str, TaskSpec] = {}
        self._results: dict[str, TaskResult] = {}

    def register(self, name: str, handler: TaskHandler, *, dependencies: tuple[str, ...] = ()) -> TaskSpec:
        spec = TaskSpec(str(name), handler, tuple(dependencies))
        self._tasks[spec.name] = spec
        return spec

    def result(self, name: str) -> TaskResult | None:
        return self._results.get(str(name))

    def results(self) -> list[TaskResult]:
        return list(self._results.values())

    def run_all(self) -> list[TaskResult]:
        for name in self._tasks:
            self.run(name)
            if self._results[name].status == "WAITING_DATASET":
                break
        return self.results()

    def run(self, name: str) -> TaskResult:
        task_name = str(name)
        if task_name in self._results:
            return self._results[task_name]
        spec = self._tasks[task_name]
        dependency_results = [self.run(dependency) for dependency in spec.dependencies]
        if any(item.status != "COMPLETED" for item in dependency_results):
            result = TaskResult(task_name, "SKIPPED", metadata={"dependencies": [item.as_dict() for item in dependency_results]})
            self._results[task_name] = result
            self._publish(KernelEventType.TASK_SKIPPED, task_name, status=result.status)
            return result
        self._publish(KernelEventType.TASK_STARTED, task_name)
        try:
            value = spec.handler()
            status = _status_from(value)
            result = TaskResult(task_name, status, value=value)
            self._results[task_name] = result
            self._publish(KernelEventType.TASK_COMPLETED, task_name, status=status)
            return result
        except Exception as error:  # pragma: no cover - defensive orchestration boundary
            result = TaskResult(task_name, "FAILED", error=f"{type(error).__name__}: {error}")
            self._results[task_name] = result
            self._publish(KernelEventType.FAILED, task_name, error=result.error)
            return result

    def _publish(self, event: str, task: str, **payload: Any) -> None:
        if self.bus is not None:
            self.bus.publish(event, f"Task {task}: {event.lower()}.", task=task, **payload)


def _status_from(value: Any) -> str:
    if isinstance(value, Mapping):
        state = value.get("state")
        if state == "WAITING_DATASET":
            return "WAITING_DATASET"
        if state in {"FAILED", "ERROR"}:
            return "FAILED"
    return "COMPLETED"


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


__all__ = ["TaskHandler", "TaskResult", "TaskScheduler", "TaskSpec"]
