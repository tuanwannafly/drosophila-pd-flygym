"""Persistent campaign and experiment history."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .campaign_events import CampaignEvent


@dataclass
class CampaignHistory:
    """Append-only in-memory history with JSON persistence."""

    campaign_id: str
    events: list[CampaignEvent] = field(default_factory=list)

    def append(self, event: CampaignEvent) -> CampaignEvent:
        if event.campaign_id != self.campaign_id:
            raise ValueError("event belongs to a different campaign")
        self.events.append(event)
        return event

    def extend(self, events: Iterable[CampaignEvent]) -> None:
        for event in events:
            self.append(event)

    def as_dict(self) -> dict[str, object]:
        return {"campaign_id": self.campaign_id, "events": [event.as_dict() for event in self.events]}

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> "CampaignHistory":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        history = cls(str(data["campaign_id"]))
        history.extend(CampaignEvent.from_dict(item) for item in data.get("events", ()))
        return history


__all__ = ["CampaignHistory"]
