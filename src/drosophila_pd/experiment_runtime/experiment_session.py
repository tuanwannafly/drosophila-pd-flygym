"""Persisted experiment session state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping
import uuid


class SessionState:
    WAITING_DATASET = "WAITING_DATASET"
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ExperimentSession:
    """Session identity and lifecycle metadata, excluding scientific arrays."""

    experiment_id: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    state: str = SessionState.WAITING_DATASET
    dataset_ids: list[str] = field(default_factory=list)
    campaign: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_timestamp)
    updated_at: str = field(default_factory=utc_timestamp)
    duration_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def set_state(self, state: str) -> None:
        self.state = str(state)
        self.updated_at = utc_timestamp()

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_version": 1,
            "experiment_id": self.experiment_id,
            "session_id": self.session_id,
            "state": self.state,
            "dataset_ids": list(self.dataset_ids),
            "campaign": dict(self.campaign),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "duration_seconds": self.duration_seconds,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "scientific_scope": "Runtime orchestration only; no simulation or biological validation claim.",
        }

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentSession":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            experiment_id=str(payload["experiment_id"]),
            session_id=str(payload["session_id"]),
            state=str(payload.get("state", SessionState.WAITING_DATASET)),
            dataset_ids=[str(item) for item in payload.get("dataset_ids", ())],
            campaign=dict(payload.get("campaign", {})),
            created_at=str(payload.get("created_at", utc_timestamp())),
            updated_at=str(payload.get("updated_at", utc_timestamp())),
            duration_seconds=float(payload.get("duration_seconds", 0.0)),
            warnings=[str(item) for item in payload.get("warnings", ())],
            errors=[str(item) for item in payload.get("errors", ())],
        )


__all__ = ["ExperimentSession", "SessionState"]
