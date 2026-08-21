"""Resolved paths and identifiers for one experiment session."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExperimentContext:
    """Filesystem context; it contains no rollout arrays or simulation state."""

    repository_root: Path
    experiment_id: str = "experimental_campaign_01_healthy_baseline"
    campaign_root: Path | None = None
    dataset_roots: tuple[Path, ...] | None = None
    output_root: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.repository_root = Path(self.repository_root).resolve()
        self.campaign_root = Path(self.campaign_root or self.repository_root / "research" / "campaigns").resolve()
        self.dataset_roots = tuple(
            Path(path).resolve()
            for path in (self.dataset_roots or (self.repository_root / "datasets", self.repository_root / "research" / "datasets"))
        )
        self.output_root = Path(
            self.output_root or self.repository_root / "results" / "experiments" / self.experiment_id
        ).resolve()

    @property
    def campaign_config_path(self) -> Path:
        candidates = (
            self.campaign_root / self.experiment_id / "campaign.yaml",
            self.campaign_root / "healthy_baseline" / "campaign.yaml",
        )
        return next((path for path in candidates if path.is_file()), candidates[0])

    def as_dict(self) -> dict[str, Any]:
        return {
            "repository_root": self.repository_root.as_posix(),
            "experiment_id": self.experiment_id,
            "campaign_root": self.campaign_root.as_posix(),
            "dataset_roots": [path.as_posix() for path in self.dataset_roots],
            "output_root": self.output_root.as_posix(),
            "metadata": dict(self.metadata),
        }


__all__ = ["ExperimentContext"]
