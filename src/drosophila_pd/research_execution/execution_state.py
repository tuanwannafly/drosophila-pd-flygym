"""State machine values for the V6 execution runtime."""

from __future__ import annotations

from enum import Enum


class ExecutionState(str, Enum):
    """Lifecycle state of one execution request."""

    WAITING_DATASET = "WAITING_DATASET"
    INVALID_DATASET = "INVALID_DATASET"
    READY = "READY"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    EXPORTING = "EXPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


ALLOWED_TRANSITIONS = {
    ExecutionState.WAITING_DATASET: {ExecutionState.INVALID_DATASET, ExecutionState.READY, ExecutionState.CANCELLED},
    ExecutionState.INVALID_DATASET: {ExecutionState.WAITING_DATASET, ExecutionState.READY, ExecutionState.CANCELLED},
    ExecutionState.READY: {ExecutionState.RUNNING, ExecutionState.CANCELLED},
    ExecutionState.RUNNING: {ExecutionState.VALIDATING, ExecutionState.FAILED, ExecutionState.CANCELLED},
    ExecutionState.VALIDATING: {ExecutionState.EXPORTING, ExecutionState.FAILED, ExecutionState.CANCELLED},
    ExecutionState.EXPORTING: {ExecutionState.COMPLETED, ExecutionState.FAILED},
    ExecutionState.FAILED: {ExecutionState.READY, ExecutionState.CANCELLED},
    ExecutionState.COMPLETED: set(),
    ExecutionState.CANCELLED: set(),
}


def coerce_state(value: ExecutionState | str) -> ExecutionState:
    """Convert serialized state text to :class:`ExecutionState`."""

    return value if isinstance(value, ExecutionState) else ExecutionState(str(value).upper())


__all__ = ["ALLOWED_TRANSITIONS", "ExecutionState", "coerce_state"]
