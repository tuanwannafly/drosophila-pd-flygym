"""Common interfaces for analysis-only behavioral assays."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np


IMPLEMENTED = "implemented"
PLANNED = "planned"


@dataclass(frozen=True)
class AssayMetricSpec:
    """Describe whether an assay metric is implemented or planned."""

    name: str
    status: str
    description: str
    required_inputs: tuple[str, ...] = ()
    limitation: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "description": self.description,
            "required_inputs": list(self.required_inputs),
            "limitation": self.limitation,
        }


@dataclass(frozen=True)
class RolloutAssayInput:
    """Rollout outputs consumed by behavioral assays.

    This container intentionally stores arrays and metadata only. It does not
    own FlyGym, MuJoCo, controller, perturbation, or simulation objects.
    """

    thorax_positions: Any
    thorax_quaternions: Any
    timestep_s: float
    adhesion_outputs: Mapping[str, Sequence[float] | np.ndarray] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def validated_positions(self) -> np.ndarray:
        array = np.asarray(self.thorax_positions, dtype=float)
        if array.ndim != 2 or array.shape[1] != 3:
            raise ValueError("thorax_positions must have shape (n_samples, 3).")
        if array.shape[0] == 0 or not np.isfinite(array).all():
            raise ValueError("thorax_positions must contain finite samples.")
        return array

    def validated_quaternions(self) -> np.ndarray:
        array = np.asarray(self.thorax_quaternions, dtype=float)
        if array.ndim != 2 or array.shape[1] != 4:
            raise ValueError("thorax_quaternions must have shape (n_samples, 4).")
        if array.shape[0] == 0 or not np.isfinite(array).all():
            raise ValueError("thorax_quaternions must contain finite samples.")
        return array

    def validated_timestep(self) -> float:
        timestep = float(self.timestep_s)
        if not np.isfinite(timestep) or timestep <= 0:
            raise ValueError("timestep_s must be a positive finite number.")
        return timestep


@dataclass(frozen=True)
class AssayResult:
    """Structured assay output with scientific-boundary metadata."""

    assay_name: str
    metrics: Mapping[str, Any]
    implemented_metrics: tuple[AssayMetricSpec, ...]
    planned_metrics: tuple[AssayMetricSpec, ...] = ()
    scientific_scope: str = (
        "Computational behavioral assay over existing rollout outputs only; "
        "not Parkinson diagnosis, biological validation, disease severity, or "
        "mechanistic evidence."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "assay_name": self.assay_name,
            "scientific_scope": self.scientific_scope,
            "implemented_metrics": [
                metric.as_dict() for metric in self.implemented_metrics
            ],
            "planned_metrics": [metric.as_dict() for metric in self.planned_metrics],
            "metrics": dict(self.metrics),
        }


class BehavioralAssay(ABC):
    """Common analysis-only behavioral assay interface."""

    name: str

    @abstractmethod
    def specification(self) -> dict[str, Any]:
        """Return metric and input metadata without evaluating a rollout."""

    @abstractmethod
    def evaluate(self, rollout: RolloutAssayInput) -> AssayResult:
        """Compute assay metrics from existing rollout outputs."""


def metric_names(metrics: Sequence[AssayMetricSpec]) -> list[str]:
    """Return metric names for compact summaries."""

    return [metric.name for metric in metrics]


__all__ = [
    "IMPLEMENTED",
    "PLANNED",
    "AssayMetricSpec",
    "AssayResult",
    "BehavioralAssay",
    "RolloutAssayInput",
    "metric_names",
]
