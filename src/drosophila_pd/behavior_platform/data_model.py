"""Session07/08 behavioral neuroscience platform data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class BehaviorEpisode:
    episode_id: str
    behavior_type: str
    start_time_s: float
    end_time_s: float
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        return max(0.0, float(self.end_time_s) - float(self.start_time_s))

    def as_dict(self) -> dict[str, Any]:
        return {
            "episode_id": self.episode_id,
            "behavior_type": self.behavior_type,
            "start_time_s": float(self.start_time_s),
            "end_time_s": float(self.end_time_s),
            "duration_s": self.duration_s,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class BehaviorSequence:
    sequence_id: str
    episodes: Sequence[BehaviorEpisode]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "sequence_id": self.sequence_id,
            "episodes": [episode.as_dict() for episode in self.episodes],
            "episode_count": len(self.episodes),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ArenaZone:
    name: str
    shape: str
    center_xy_mm: tuple[float, float] = (0.0, 0.0)
    radius_mm: float | None = None
    size_xy_mm: tuple[float, float] | None = None
    polygon_xy_mm: tuple[tuple[float, float], ...] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "shape": self.shape,
            "center_xy_mm": list(self.center_xy_mm),
            "radius_mm": self.radius_mm,
            "size_xy_mm": list(self.size_xy_mm) if self.size_xy_mm else None,
            "polygon_xy_mm": [list(point) for point in self.polygon_xy_mm]
            if self.polygon_xy_mm
            else None,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class Arena:
    arena_id: str
    shape: str = "rectangle"
    center_xy_mm: tuple[float, float] = (0.0, 0.0)
    radius_mm: float | None = None
    size_xy_mm: tuple[float, float] | None = (100.0, 100.0)
    border_width_mm: float = 10.0
    center_fraction: float = 0.5
    zones: Sequence[ArenaZone] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def rectangular(
        cls,
        *,
        arena_id: str = "rectangular_open_field",
        size_xy_mm: tuple[float, float] = (100.0, 100.0),
        border_width_mm: float = 10.0,
        center_fraction: float = 0.5,
        zones: Sequence[ArenaZone] = (),
    ) -> "Arena":
        return cls(
            arena_id=arena_id,
            shape="rectangle",
            size_xy_mm=size_xy_mm,
            border_width_mm=border_width_mm,
            center_fraction=center_fraction,
            zones=tuple(zones),
        )

    @classmethod
    def circular(
        cls,
        *,
        arena_id: str = "circular_open_field",
        radius_mm: float = 50.0,
        border_width_mm: float = 10.0,
        center_fraction: float = 0.5,
        zones: Sequence[ArenaZone] = (),
    ) -> "Arena":
        return cls(
            arena_id=arena_id,
            shape="circle",
            radius_mm=radius_mm,
            size_xy_mm=None,
            border_width_mm=border_width_mm,
            center_fraction=center_fraction,
            zones=tuple(zones),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "arena_id": self.arena_id,
            "shape": self.shape,
            "center_xy_mm": list(self.center_xy_mm),
            "radius_mm": self.radius_mm,
            "size_xy_mm": list(self.size_xy_mm) if self.size_xy_mm else None,
            "border_width_mm": float(self.border_width_mm),
            "center_fraction": float(self.center_fraction),
            "zones": [zone.as_dict() for zone in self.zones],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ProgressionStage:
    name: str
    index: int
    computational_parameters: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "index": int(self.index),
            "computational_parameters": dict(self.computational_parameters),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ProgressionTimeline:
    timeline_id: str
    stages: Sequence[ProgressionStage]
    stage_times_s: Sequence[float]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "timeline_id": self.timeline_id,
            "stages": [stage.as_dict() for stage in self.stages],
            "stage_times_s": [float(value) for value in self.stage_times_s],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class BehaviorComparison:
    comparison_id: str
    conditions: Sequence[str]
    similarity_matrix: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "conditions": list(self.conditions),
            "similarity_matrix": dict(self.similarity_matrix),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class BehaviorReport:
    report_id: str
    sections: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "sections": dict(self.sections),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class BehaviorDashboard:
    dashboard_id: str
    panels: Sequence[str]
    filters: Mapping[str, Any] = field(default_factory=dict)
    exports: Mapping[str, str] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dashboard_id": self.dashboard_id,
            "panels": list(self.panels),
            "filters": dict(self.filters),
            "exports": dict(self.exports),
            "metadata": dict(self.metadata),
        }


__all__ = [
    "Arena",
    "ArenaZone",
    "BehaviorComparison",
    "BehaviorDashboard",
    "BehaviorEpisode",
    "BehaviorReport",
    "BehaviorSequence",
    "ProgressionStage",
    "ProgressionTimeline",
]
