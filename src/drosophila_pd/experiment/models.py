"""Data models for real experiment orchestration.

The models describe jobs and provenance. They do not contain FlyGym or MuJoCo
execution logic; those integrations are supplied by explicit stage handlers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


SCIENTIFIC_SCOPE = (
    "Computational experiment orchestration and data management only; "
    "no biological validation or Parkinson's disease claim."
)

STAGE_NAMES = (
    "rollout",
    "digital_fly",
    "motion_3d",
    "analysis",
    "computational_pd",
    "scientific_validation",
    "publication_export",
)

ARTIFACT_DIRECTORIES = (
    "rollout",
    "digital_fly",
    "analysis",
    "statistics",
    "validation",
    "figures",
    "reports",
    "logs",
    "publication",
)


class ExperimentStatus(str, Enum):
    """Lifecycle states for one experiment job."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass
class ExperimentJob:
    """A caller-configured experiment and its output location."""

    job_id: str
    config: Mapping[str, Any]
    output_root: Path | str
    max_retries: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    status: ExperimentStatus = ExperimentStatus.PENDING
    attempts: int = 0
    created_at: str = field(default_factory=utc_timestamp)
    updated_at: str = field(default_factory=utc_timestamp)

    def __post_init__(self) -> None:
        if not self.job_id.strip():
            raise ValueError("job_id is required")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self.output_root = Path(self.output_root)
        if isinstance(self.status, str):
            self.status = ExperimentStatus(self.status)

    @property
    def job_root(self) -> Path:
        return Path(self.output_root) / self.job_id

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "config": _jsonable(self.config),
            "output_root": str(self.output_root),
            "max_retries": int(self.max_retries),
            "metadata": _jsonable(self.metadata),
            "status": self.status.value,
            "attempts": int(self.attempts),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "scientific_scope": SCIENTIFIC_SCOPE,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExperimentJob":
        return cls(
            job_id=str(data["job_id"]),
            config=dict(data.get("config", {})),
            output_root=Path(str(data["output_root"])),
            max_retries=int(data.get("max_retries", 0)),
            metadata=dict(data.get("metadata", {})),
            status=ExperimentStatus(str(data.get("status", ExperimentStatus.PENDING.value))),
            attempts=int(data.get("attempts", 0)),
            created_at=str(data.get("created_at", utc_timestamp())),
            updated_at=str(data.get("updated_at", utc_timestamp())),
        )


@dataclass(frozen=True)
class ExperimentManifest:
    """Immutable-at-write metadata describing one attempted experiment."""

    job_id: str
    status: ExperimentStatus
    attempt: int
    stages: Mapping[str, Any]
    artifact_hashes: Mapping[str, str]
    configuration_hash: str
    git_commit: str
    started_at: str
    finished_at: str
    error: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    scientific_scope: str = SCIENTIFIC_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": 1,
            "job_id": self.job_id,
            "status": self.status.value,
            "attempt": int(self.attempt),
            "stages": _jsonable(self.stages),
            "artifact_hashes": dict(sorted(self.artifact_hashes.items())),
            "configuration_hash": self.configuration_hash,
            "git_commit": self.git_commit,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
            "metadata": _jsonable(self.metadata),
            "scientific_scope": self.scientific_scope,
        }


@dataclass(frozen=True)
class ExperimentResult:
    """Result returned by :class:`ExperimentRunner`."""

    job_id: str
    status: ExperimentStatus
    stages: Mapping[str, Any]
    artifact_paths: Mapping[str, str]
    manifest_path: Path
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "stages": _jsonable(self.stages),
            "artifact_paths": dict(sorted(self.artifact_paths.items())),
            "manifest_path": str(self.manifest_path),
            "error": self.error,
            "scientific_scope": SCIENTIFIC_SCOPE,
        }


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"stage output is not JSON-compatible: {type(value).__name__}")


__all__ = [
    "ARTIFACT_DIRECTORIES",
    "ExperimentJob",
    "ExperimentManifest",
    "ExperimentResult",
    "ExperimentStatus",
    "SCIENTIFIC_SCOPE",
    "STAGE_NAMES",
    "utc_timestamp",
]
