"""Campaign metadata and explicit experiment plans.

This module describes work; it never executes simulation or analysis code.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
import uuid

from drosophila_pd.behavior_platform.campaign_provenance import stable_hash

from .campaign_state import CampaignState, coerce_state
from .campaign_events import utc_timestamp


CAMPAIGN_SCOPE = (
    "Research campaign orchestration over existing computational artifacts only; "
    "no FlyGym execution, fabricated rollout, new metric, or biological claim."
)


@dataclass
class ExperimentSpec:
    """One scheduled experiment supplied to an external executor."""

    experiment_id: str
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    dependencies: tuple[str, ...] = ()
    batch: str = "default"
    state: CampaignState = CampaignState.QUEUED
    attempts: int = 0
    result_path: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.experiment_id.strip() or not self.name.strip():
            raise ValueError("experiment_id and name are required")
        self.dependencies = tuple(str(item) for item in self.dependencies)
        self.state = coerce_state(self.state)
        if self.priority != int(self.priority):
            raise ValueError("priority must be an integer")
        self.priority = int(self.priority)

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "name": self.name,
            "config": _jsonable(self.config),
            "priority": self.priority,
            "dependencies": list(self.dependencies),
            "batch": self.batch,
            "state": self.state.value,
            "attempts": self.attempts,
            "result_path": self.result_path,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExperimentSpec":
        return cls(
            experiment_id=str(data["experiment_id"]),
            name=str(data["name"]),
            config=dict(data.get("config", {})),
            priority=int(data.get("priority", 0)),
            dependencies=tuple(data.get("dependencies", ())),
            batch=str(data.get("batch", "default")),
            state=data.get("state", CampaignState.QUEUED.value),
            attempts=int(data.get("attempts", 0)),
            result_path=data.get("result_path"),
            error=data.get("error"),
        )


@dataclass
class Campaign:
    """A persisted campaign definition and its experiment matrix."""

    name: str
    description: str = ""
    author: str = ""
    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_time: str = field(default_factory=utc_timestamp)
    updated_time: str = field(default_factory=utc_timestamp)
    status: CampaignState = CampaignState.QUEUED
    datasets: list[str] = field(default_factory=list)
    experiments: list[ExperimentSpec] = field(default_factory=list)
    validation_profile: dict[str, Any] = field(default_factory=dict)
    report_profile: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("campaign name is required")
        self.status = coerce_state(self.status)

    @property
    def configuration_hash(self) -> str:
        return stable_hash(self.configuration())

    def configuration(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "datasets": list(self.datasets),
            "experiments": [experiment.as_dict() for experiment in self.experiments],
            "validation_profile": _jsonable(self.validation_profile),
            "report_profile": _jsonable(self.report_profile),
            "tags": list(self.tags),
            "notes": self.notes,
            "metadata": _jsonable(self.metadata),
        }

    def add_experiment(self, experiment: ExperimentSpec) -> ExperimentSpec:
        if any(item.experiment_id == experiment.experiment_id for item in self.experiments):
            raise ValueError(f"duplicate experiment_id: {experiment.experiment_id}")
        self.experiments.append(experiment)
        self.touch()
        return experiment

    def touch(self) -> None:
        self.updated_time = utc_timestamp()

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "created_time": self.created_time,
            "updated_time": self.updated_time,
            "status": self.status.value,
            "datasets": list(self.datasets),
            "experiments": [experiment.as_dict() for experiment in self.experiments],
            "validation_profile": _jsonable(self.validation_profile),
            "report_profile": _jsonable(self.report_profile),
            "tags": list(self.tags),
            "notes": self.notes,
            "metadata": _jsonable(self.metadata),
            "configuration_hash": self.configuration_hash,
            "scientific_scope": CAMPAIGN_SCOPE,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Campaign":
        campaign = cls(
            campaign_id=str(data["campaign_id"]),
            name=str(data["name"]),
            description=str(data.get("description", "")),
            author=str(data.get("author", "")),
            created_time=str(data.get("created_time", utc_timestamp())),
            updated_time=str(data.get("updated_time", utc_timestamp())),
            status=data.get("status", CampaignState.QUEUED.value),
            datasets=[str(item) for item in data.get("datasets", ())],
            validation_profile=dict(data.get("validation_profile", {})),
            report_profile=dict(data.get("report_profile", {})),
            tags=[str(item) for item in data.get("tags", ())],
            notes=str(data.get("notes", "")),
            metadata=dict(data.get("metadata", {})),
        )
        campaign.experiments = [ExperimentSpec.from_dict(item) for item in data.get("experiments", ())]
        return campaign

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path) -> "Campaign":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _jsonable(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


__all__ = ["CAMPAIGN_SCOPE", "Campaign", "ExperimentSpec"]
