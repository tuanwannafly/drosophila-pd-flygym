"""Persistent state transition history for execution requests."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .execution_state import ALLOWED_TRANSITIONS, ExecutionState, coerce_state


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class ExecutionEvent:
    """One immutable state or diagnostic event."""

    event: str
    timestamp: str = field(default_factory=utc_timestamp)
    state: ExecutionState | None = None
    message: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "timestamp": self.timestamp,
            "state": self.state.value if self.state is not None else None,
            "message": self.message,
            "metadata": _jsonable(self.metadata),
        }


class ExecutionHistory:
    """Track and validate the explicit V6 state machine."""

    def __init__(self, initial_state: ExecutionState = ExecutionState.WAITING_DATASET) -> None:
        self.state = coerce_state(initial_state)
        self.events: list[ExecutionEvent] = [ExecutionEvent("initialized", state=self.state)]

    def record(self, event: str, message: str = "", **metadata: Any) -> ExecutionEvent:
        item = ExecutionEvent(event, state=self.state, message=message, metadata=metadata)
        self.events.append(item)
        return item

    def transition(self, target: ExecutionState | str, message: str = "", **metadata: Any) -> ExecutionEvent:
        next_state = coerce_state(target)
        if next_state not in ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"invalid execution transition: {self.state.value} -> {next_state.value}")
        previous = self.state
        self.state = next_state
        item = ExecutionEvent(
            "state_transition",
            state=next_state,
            message=message,
            metadata={"from": previous.value, **metadata},
        )
        self.events.append(item)
        return item

    def as_dict(self) -> dict[str, Any]:
        return {"state": self.state.value, "events": [event.as_dict() for event in self.events]}

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> "ExecutionHistory":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        history = cls(coerce_state(payload["state"]))
        history.events = [
            ExecutionEvent(
                event=str(item["event"]),
                timestamp=str(item.get("timestamp", utc_timestamp())),
                state=coerce_state(item["state"]) if item.get("state") else None,
                message=str(item.get("message", "")),
                metadata=dict(item.get("metadata", {})),
            )
            for item in payload.get("events", ())
        ]
        return history


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


__all__ = ["ExecutionEvent", "ExecutionHistory", "utc_timestamp"]
