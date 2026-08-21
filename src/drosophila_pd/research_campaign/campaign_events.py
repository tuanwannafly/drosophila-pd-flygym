"""Structured events emitted by the campaign lifecycle."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping
import uuid


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class CampaignEvent:
    """One immutable lifecycle event."""

    event_type: str
    campaign_id: str
    experiment_id: str | None = None
    state: str | None = None
    author: str = ""
    timestamp: str = field(default_factory=utc_timestamp)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "campaign_id": self.campaign_id,
            "experiment_id": self.experiment_id,
            "state": self.state,
            "author": self.author,
            "timestamp": self.timestamp,
            "payload": _jsonable(self.payload),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CampaignEvent":
        return cls(
            event_id=str(data.get("event_id", uuid.uuid4())),
            event_type=str(data["event_type"]),
            campaign_id=str(data["campaign_id"]),
            experiment_id=data.get("experiment_id"),
            state=data.get("state"),
            author=str(data.get("author", "")),
            timestamp=str(data.get("timestamp", utc_timestamp())),
            payload=dict(data.get("payload", {})),
        )


def _jsonable(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


__all__ = ["CampaignEvent", "utc_timestamp"]
