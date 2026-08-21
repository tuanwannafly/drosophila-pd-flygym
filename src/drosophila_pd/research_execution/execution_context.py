"""Filesystem and provenance context for one campaign execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ExecutionContext:
    """Resolved repository paths used by the execution runtime.

    The context contains paths only. It does not load rollout arrays or hold
    simulation state.
    """

    repository_root: Path
    campaign_id: str = "experimental_campaign_01_healthy_baseline"
    campaign_root: Path | None = None
    dataset_root: Path | None = None
    output_root: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.repository_root = Path(self.repository_root).resolve()
        self.campaign_root = Path(self.campaign_root or self.repository_root / "research" / "campaigns").resolve()
        self.dataset_root = Path(self.dataset_root or self.repository_root / "datasets").resolve()
        self.output_root = Path(
            self.output_root or self.repository_root / "results" / "execution" / self.campaign_id
        ).resolve()

    @property
    def campaign_config_path(self) -> Path:
        """Return the preferred campaign configuration path."""

        candidates = (
            self.campaign_root / self.campaign_id / "campaign.yaml",
            self.campaign_root / "healthy_baseline" / "campaign.yaml",
        )
        return next((path for path in candidates if path.is_file()), candidates[0])

    @property
    def dataset_search_roots(self) -> tuple[Path, ...]:
        """Return ordered roots where real dataset manifests may be found."""

        return tuple(
            dict.fromkeys(
                (
                    self.dataset_root,
                    self.repository_root / "research" / "datasets",
                    self.repository_root / "research",
                )
            )
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "repository_root": self.repository_root.as_posix(),
            "campaign_id": self.campaign_id,
            "campaign_root": self.campaign_root.as_posix(),
            "dataset_root": self.dataset_root.as_posix(),
            "dataset_search_roots": [path.as_posix() for path in self.dataset_search_roots],
            "output_root": self.output_root.as_posix(),
            "metadata": dict(self.metadata),
        }


__all__ = ["ExecutionContext"]
