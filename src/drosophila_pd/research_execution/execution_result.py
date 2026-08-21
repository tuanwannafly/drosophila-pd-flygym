"""Serializable output model for the V6 execution runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .execution_state import ExecutionState, coerce_state


SCIENTIFIC_SCOPE = (
    "Execution orchestration over supplied computational datasets only; "
    "no fabricated rollout, simulation, or biological validation claim."
)


@dataclass
class ExecutionResult:
    """Reportable result of discovery, preparation, or execution."""

    execution_id: str
    state: ExecutionState
    datasets: list[Mapping[str, Any]] = field(default_factory=list)
    stages: list[Mapping[str, Any]] = field(default_factory=list)
    artifacts: list[Mapping[str, Any]] = field(default_factory=list)
    validation: Mapping[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    history: Mapping[str, Any] = field(default_factory=dict)
    context: Mapping[str, Any] = field(default_factory=dict)
    scientific_scope: str = SCIENTIFIC_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "state": coerce_state(self.state).value,
            "datasets": _jsonable(self.datasets),
            "stages": _jsonable(self.stages),
            "artifacts": _jsonable(self.artifacts),
            "validation": _jsonable(self.validation),
            "duration_seconds": float(self.duration_seconds),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "history": _jsonable(self.history),
            "context": _jsonable(self.context),
            "scientific_scope": self.scientific_scope,
        }


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


__all__ = ["ExecutionResult", "SCIENTIFIC_SCOPE"]
