"""Interactive laboratory abstractions for v2 behavioral experiments."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class ExperimentRecord:
    experiment_id: str
    condition: str
    artifacts: Mapping[str, str]
    metrics: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "condition": self.condition,
            "artifacts": dict(self.artifacts),
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ExperimentCatalog:
    catalog_id: str
    experiments: tuple[ExperimentRecord, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "catalog_id": self.catalog_id,
            "experiments": [experiment.as_dict() for experiment in self.experiments],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class LabLayout:
    layout_id: str
    panels: tuple[str, ...]
    selected_conditions: tuple[str, ...] = ()
    filters: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "layout_id": self.layout_id,
            "panels": list(self.panels),
            "selected_conditions": list(self.selected_conditions),
            "filters": dict(self.filters),
            "metadata": dict(self.metadata),
        }


def build_experiment_catalog(
    experiments: Sequence[ExperimentRecord | Mapping[str, Any]],
    *,
    catalog_id: str = "v2_experiment_catalog",
) -> ExperimentCatalog:
    """Build a catalog for experiment browser views."""

    records = tuple(
        item
        if isinstance(item, ExperimentRecord)
        else ExperimentRecord(
            experiment_id=str(item["experiment_id"]),
            condition=str(item["condition"]),
            artifacts=dict(item.get("artifacts", {})),
            metrics=dict(item.get("metrics", {})),
            metadata=dict(item.get("metadata", {})),
        )
        for item in experiments
    )
    return ExperimentCatalog(catalog_id=catalog_id, experiments=records)


def build_interactive_lab(
    catalog: ExperimentCatalog,
    *,
    layout: LabLayout | None = None,
) -> dict[str, Any]:
    """Build a serializable interactive laboratory specification."""

    active_layout = layout or LabLayout(
        layout_id="default_behavior_lab_layout",
        panels=(
            "experiment_browser",
            "experiment_catalog",
            "rollout_explorer",
            "synchronized_replay",
            "condition_selector",
            "trajectory_explorer",
            "timeline_explorer",
            "metric_explorer",
            "dashboard_layout_manager",
        ),
        selected_conditions=tuple(sorted({experiment.condition for experiment in catalog.experiments})),
        filters={"time_slider": True, "condition_selector": True},
    )
    return {
        "interactive_lab_version": 2,
        "scientific_scope": (
            "Interactive laboratory specification for browsing existing "
            "computational artifacts only."
        ),
        "catalog": catalog.as_dict(),
        "layout": active_layout.as_dict(),
    }


def save_lab_layout(layout: LabLayout, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(layout.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def load_lab_layout(path: str | Path) -> LabLayout:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return LabLayout(
        layout_id=str(data["layout_id"]),
        panels=tuple(data.get("panels", ())),
        selected_conditions=tuple(data.get("selected_conditions", ())),
        filters=dict(data.get("filters", {})),
        metadata=dict(data.get("metadata", {})),
    )


__all__ = [
    "ExperimentCatalog",
    "ExperimentRecord",
    "LabLayout",
    "build_experiment_catalog",
    "build_interactive_lab",
    "load_lab_layout",
    "save_lab_layout",
]
