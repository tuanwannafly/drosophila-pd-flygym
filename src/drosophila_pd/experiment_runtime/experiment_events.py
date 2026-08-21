"""Typed lifecycle events emitted by the V8 runtime."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping
from enum import Enum


class ExperimentEventType(str, Enum):
    DATASET_READY = "DATASET_READY"
    SESSION_CREATED = "SESSION_CREATED"
    PIPELINE_STARTED = "PIPELINE_STARTED"
    PIPELINE_COMPLETED = "PIPELINE_COMPLETED"
    VALIDATION_COMPLETED = "VALIDATION_COMPLETED"
    PACKAGE_CREATED = "PACKAGE_CREATED"
    FAILED = "FAILED"
    WAITING_DATASET = "WAITING_DATASET"


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class ExperimentEvent:
    """One immutable event record."""

    event: ExperimentEventType
    timestamp: str = field(default_factory=utc_timestamp)
    message: str = ""
    payload: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "event": self.event.value,
            "timestamp": self.timestamp,
            "message": self.message,
            "payload": _jsonable(self.payload),
        }


class EventLog:
    """Ordered event collection with JSON persistence."""

    def __init__(self, events: list[ExperimentEvent] | None = None) -> None:
        self.events = list(events or [])

    def emit(self, event: ExperimentEventType, message: str = "", **payload: Any) -> ExperimentEvent:
        item = ExperimentEvent(event=event, message=message, payload=payload)
        self.events.append(item)
        return item

    def as_dict(self) -> dict[str, Any]:
        return {"event_count": len(self.events), "events": [item.as_dict() for item in self.events]}

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> "EventLog":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            [
                ExperimentEvent(
                    event=ExperimentEventType(item["event"]),
                    timestamp=str(item["timestamp"]),
                    message=str(item.get("message", "")),
                    payload=dict(item.get("payload", {})),
                )
                for item in payload.get("events", ())
            ]
        )


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


__all__ = ["EventLog", "ExperimentEvent", "ExperimentEventType"]
