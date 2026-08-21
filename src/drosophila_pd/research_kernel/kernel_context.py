"""Configuration and paths for a Research Kernel instance."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class KernelContext:
    """Resolve kernel-owned operational paths without touching scientific data."""

    repository_root: Path
    kernel_id: str = "default"
    output_root: Path | None = None
    experiment_id: str = "experimental_campaign_01_healthy_baseline"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository_root", Path(self.repository_root).resolve())
        root = self.output_root or self.repository_root / "results" / "kernel" / self.kernel_id
        object.__setattr__(self, "output_root", Path(root).resolve())

    @property
    def experiment_root(self) -> Path:
        return self.output_root / "experiment"

    @property
    def kernel_log(self) -> Path:
        return self.output_root / "kernel.log"

    @property
    def events_path(self) -> Path:
        return self.output_root / "events.json"

    @property
    def timeline_path(self) -> Path:
        return self.output_root / "timeline.json"

    @property
    def state_path(self) -> Path:
        return self.output_root / "kernel_state.json"

    @property
    def resources_path(self) -> Path:
        return self.output_root / "resources.json"

    @property
    def registry_path(self) -> Path:
        return self.output_root / "registry.json"

    def as_dict(self) -> dict[str, Any]:
        return {
            "kernel_id": self.kernel_id,
            "repository_root": self.repository_root.as_posix(),
            "output_root": self.output_root.as_posix(),
            "experiment_id": self.experiment_id,
            "metadata": dict(self.metadata),
        }


__all__ = ["KernelContext"]
