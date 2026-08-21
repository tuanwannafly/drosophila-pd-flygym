"""Event bus and durable event records for the Research Kernel."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Mapping


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


class KernelEventType:
    """Canonical cross-subsystem event names."""

    KERNEL_BOOTED = "KERNEL_BOOTED"
    KERNEL_READY = "KERNEL_READY"
    DATASET_READY = "DATASET_READY"
    SESSION_CREATED = "SESSION_CREATED"
    CAMPAIGN_STARTED = "CAMPAIGN_STARTED"
    STUDY_COMPLETED = "STUDY_COMPLETED"
    PACKAGE_CREATED = "PACKAGE_CREATED"
    ARCHIVED = "ARCHIVED"
    WAITING_DATASET = "WAITING_DATASET"
    TASK_STARTED = "TASK_STARTED"
    TASK_COMPLETED = "TASK_COMPLETED"
    TASK_SKIPPED = "TASK_SKIPPED"
    KERNEL_SHUTDOWN = "KERNEL_SHUTDOWN"
    FAILED = "FAILED"


@dataclass(frozen=True)
class KernelEvent:
    """One event published on the research bus."""

    event: str
    message: str = ""
    timestamp: str = field(default_factory=utc_timestamp)
    payload: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "message": self.message,
            "timestamp": self.timestamp,
            "payload": _jsonable(self.payload),
        }


Subscriber = Callable[[KernelEvent], None]


class ResearchBus:
    """In-process pub/sub bus with an append-only persisted event history."""

    def __init__(self, events: list[KernelEvent] | None = None) -> None:
        self._events = list(events or [])
        self._subscribers: dict[str | None, list[Subscriber]] = {}

    def subscribe(self, callback: Subscriber, event: str | None = None) -> None:
        self._subscribers.setdefault(event, []).append(callback)

    def publish(self, event: str, message: str = "", **payload: Any) -> KernelEvent:
        record = KernelEvent(event=str(event), message=message, payload=payload)
        self._events.append(record)
        for callback in [*self._subscribers.get(None, ()), *self._subscribers.get(record.event, ())]:
            callback(record)
        return record

    def records(self) -> list[KernelEvent]:
        return list(self._events)

    def as_dict(self) -> dict[str, Any]:
        return {"event_schema_version": 1, "events": [event.as_dict() for event in self._events]}

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> "ResearchBus":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        events = [
            KernelEvent(
                event=str(item["event"]),
                message=str(item.get("message", "")),
                timestamp=str(item.get("timestamp", utc_timestamp())),
                payload=dict(item.get("payload", {})),
            )
            for item in payload.get("events", ())
        ]
        return cls(events)


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


__all__ = ["KernelEvent", "KernelEventType", "ResearchBus"]
