"""Data models for large-scale campaign planning and tracking."""

from __future__ import annotations

import platform
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Mapping

from drosophila_pd.behavior_platform.campaign_provenance import stable_hash


CAMPAIGN_SCOPE = "Campaign orchestration over real computational artifacts only; no simulation or biological claim."


class CampaignStatus(str, Enum):
    PLANNED = "PLANNED"
    READY = "READY"
    WAITING_DATASET = "WAITING_DATASET"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


@dataclass
class CampaignProgress:
    """Operational progress counters derived from a campaign matrix."""

    total: int = 0
    completed: int = 0
    failed: int = 0
    waiting: int = 0
    queued: int = 0
    running: int = 0
    runtime_estimate_s: float | None = None
    storage_bytes: int = 0
    artifact_count: int = 0
    validation_status: str = "PENDING"
    publication_readiness: str = "PLANNING_ONLY"

    @property
    def fraction(self) -> float:
        return self.completed / self.total if self.total else 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "waiting": self.waiting,
            "queued": self.queued,
            "running": self.running,
            "completion_fraction": self.fraction,
            "runtime_estimate_s": self.runtime_estimate_s,
            "storage_bytes": self.storage_bytes,
            "artifact_count": self.artifact_count,
            "validation_status": self.validation_status,
            "publication_readiness": self.publication_readiness,
        }


@dataclass
class CampaignSummary:
    """Compact campaign status view."""

    campaign_id: str
    name: str
    status: CampaignStatus
    progress: CampaignProgress
    datasets: tuple[str, ...] = ()
    expected_outputs: tuple[str, ...] = ()
    scientific_scope: str = CAMPAIGN_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "status": self.status.value,
            "datasets": list(self.datasets),
            "expected_outputs": list(self.expected_outputs),
            "progress": self.progress.as_dict(),
            "scientific_scope": self.scientific_scope,
        }


@dataclass(frozen=True)
class CampaignManifest:
    """Reproducibility and artifact provenance for a campaign plan."""

    campaign_id: str
    configuration_hash: str
    source_commit: str
    branch: str
    python: str
    datasets: tuple[str, ...] = ()
    dataset_hashes: Mapping[str, str] = field(default_factory=dict)
    artifact_hashes: Mapping[str, str] = field(default_factory=dict)
    random_seeds: tuple[int, ...] = ()
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    scientific_scope: str = CAMPAIGN_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": 1,
            "campaign_id": self.campaign_id,
            "configuration_hash": self.configuration_hash,
            "source_commit": self.source_commit,
            "branch": self.branch,
            "python": self.python,
            "datasets": list(self.datasets),
            "dataset_hashes": dict(sorted(self.dataset_hashes.items())),
            "artifact_hashes": dict(sorted(self.artifact_hashes.items())),
            "random_seeds": list(self.random_seeds),
            "timestamp": self.timestamp,
            "scientific_scope": self.scientific_scope,
        }


@dataclass
class CampaignHistory:
    """Append-only lifecycle event history."""

    campaign_id: str
    events: list[dict[str, Any]] = field(default_factory=list)

    def append(self, event: str, *, status: CampaignStatus | None = None, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        record = {
            "event": event,
            "campaign_id": self.campaign_id,
            "status": status.value if isinstance(status, CampaignStatus) else status,
            "timestamp": datetime.now(UTC).isoformat(),
            "payload": dict(payload or {}),
        }
        self.events.append(record)
        return record

    def as_dict(self) -> dict[str, Any]:
        return {"campaign_id": self.campaign_id, "events": list(self.events)}


@dataclass
class CampaignQueue:
    """Deterministic campaign queue ordered by priority then campaign ID."""

    campaign_ids: list[str] = field(default_factory=list)

    def enqueue(self, campaign_id: str) -> None:
        if campaign_id not in self.campaign_ids:
            self.campaign_ids.append(campaign_id)

    def remove(self, campaign_id: str) -> None:
        self.campaign_ids = [item for item in self.campaign_ids if item != campaign_id]

    def peek(self) -> str | None:
        return self.campaign_ids[0] if self.campaign_ids else None

    def as_dict(self) -> dict[str, Any]:
        return {"campaign_ids": list(self.campaign_ids)}


@dataclass
class Campaign:
    """A campaign definition with a reproducible execution matrix."""

    name: str
    campaign_type: str = "custom"
    description: str = ""
    author: str = ""
    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: CampaignStatus = CampaignStatus.PLANNED
    datasets: list[str] = field(default_factory=list)
    matrix: list[dict[str, Any]] = field(default_factory=list)
    expected_outputs: list[str] = field(default_factory=list)
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    artifacts: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("campaign name is required")
        self.status = self.status if isinstance(self.status, CampaignStatus) else CampaignStatus(str(self.status).upper())
        self.priority = int(self.priority)

    @property
    def configuration_hash(self) -> str:
        return stable_hash(self.configuration())

    def configuration(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "campaign_type": self.campaign_type,
            "description": self.description,
            "datasets": list(self.datasets),
            "matrix": _jsonable(self.matrix),
            "expected_outputs": list(self.expected_outputs),
            "priority": self.priority,
            "metadata": _jsonable(self.metadata),
        }

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC).isoformat()

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "campaign_type": self.campaign_type,
            "description": self.description,
            "author": self.author,
            "status": self.status.value,
            "datasets": list(self.datasets),
            "matrix": _jsonable(self.matrix),
            "expected_outputs": list(self.expected_outputs),
            "priority": self.priority,
            "metadata": _jsonable(self.metadata),
            "artifacts": list(self.artifacts),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "configuration_hash": self.configuration_hash,
            "scientific_scope": CAMPAIGN_SCOPE,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Campaign":
        return cls(
            campaign_id=str(data["campaign_id"]),
            name=str(data["name"]),
            campaign_type=str(data.get("campaign_type", "custom")),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            status=data.get("status", CampaignStatus.PLANNED.value),
            datasets=[str(item) for item in data.get("datasets", ())],
            matrix=[dict(item) for item in data.get("matrix", ()) if isinstance(item, Mapping)],
            expected_outputs=[str(item) for item in data.get("expected_outputs", ())],
            priority=int(data.get("priority", 0)),
            metadata=dict(data.get("metadata", {})),
            artifacts=[str(item) for item in data.get("artifacts", ())],
            created_at=str(data.get("created_at", datetime.now(UTC).isoformat())),
            updated_at=str(data.get("updated_at", datetime.now(UTC).isoformat())),
        )


def current_provenance(campaign: Campaign, *, artifacts: Mapping[str, str] | None = None) -> CampaignManifest:
    """Collect lightweight provenance without importing simulation packages."""

    return CampaignManifest(
        campaign_id=campaign.campaign_id,
        configuration_hash=campaign.configuration_hash,
        source_commit=_git_value(("rev-parse", "HEAD")),
        branch=_git_value(("branch", "--show-current")),
        python=platform.python_version(),
        datasets=tuple(campaign.datasets),
        artifact_hashes=dict(artifacts or {}),
        random_seeds=tuple(sorted({int(row["seed"]) for row in campaign.matrix if row.get("seed") is not None})),
    )


def _git_value(args: tuple[str, ...]) -> str:
    try:
        return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _jsonable(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


__all__ = [
    "CAMPAIGN_SCOPE",
    "Campaign",
    "CampaignHistory",
    "CampaignManifest",
    "CampaignProgress",
    "CampaignQueue",
    "CampaignStatus",
    "CampaignSummary",
    "current_provenance",
]
