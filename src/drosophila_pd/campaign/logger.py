"""Structured campaign lifecycle logging."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


class CampaignLogger:
    """Append JSON event records to an explicit caller-selected file."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def log(self, event: str, *, campaign_id: str, status: str, payload: Mapping[str, Any] | None = None) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "event": event,
            "campaign_id": campaign_id,
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": dict(payload or {}),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return self.path


__all__ = ["CampaignLogger"]
