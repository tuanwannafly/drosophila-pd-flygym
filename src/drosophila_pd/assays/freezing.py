"""Freezing-style assay over existing speed and bout outputs."""

from __future__ import annotations

from typing import Any

from drosophila_pd.assays.base import (
    IMPLEMENTED,
    AssayMetricSpec,
    AssayResult,
    BehavioralAssay,
    RolloutAssayInput,
)
from drosophila_pd.metrics.bouts import compute_walking_bout_metrics
from drosophila_pd.metrics.trajectory import compute_trajectory_timeseries


FREEZING_IMPLEMENTED_METRICS = (
    AssayMetricSpec(
        name="pause_duration",
        status=IMPLEMENTED,
        description="Total time below the configured immobility speed threshold.",
        required_inputs=("thorax_positions", "timestep_s"),
    ),
    AssayMetricSpec(
        name="pause_frequency",
        status=IMPLEMENTED,
        description="Detected pause episodes per second.",
        required_inputs=("thorax_positions", "timestep_s"),
    ),
    AssayMetricSpec(
        name="immobility_ratio",
        status=IMPLEMENTED,
        description="Fraction of analyzed time classified as immobile.",
        required_inputs=("thorax_positions", "timestep_s"),
    ),
    AssayMetricSpec(
        name="freezing_episode_detection",
        status=IMPLEMENTED,
        description="Pause bouts meeting the configured minimum duration.",
        required_inputs=("thorax_positions", "timestep_s"),
    ),
)


class FreezingAssay(BehavioralAssay):
    """Detect computational freezing episodes from trajectory speed."""

    name = "freezing"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = {
            "immobility_speed_threshold_mm_s": 1.0,
            "min_freezing_duration_s": 0.0,
            **(config or {}),
        }

    def specification(self) -> dict[str, Any]:
        return {
            "assay_name": self.name,
            "implemented_metrics": [
                metric.as_dict() for metric in FREEZING_IMPLEMENTED_METRICS
            ],
            "planned_metrics": [],
            "configuration": dict(self.config),
        }

    def evaluate(self, rollout: RolloutAssayInput) -> AssayResult:
        positions = rollout.validated_positions()
        quaternions = rollout.validated_quaternions()
        timestep = rollout.validated_timestep()
        trajectory = compute_trajectory_timeseries(
            thorax_positions=positions,
            thorax_quaternions=quaternions,
            timestep_s=timestep,
        )
        bout_metrics = compute_walking_bout_metrics(
            step_speed_mm_s=trajectory["step_speed_mm_s"],
            timestep_s=timestep,
            speed_threshold_mm_s=self.config["immobility_speed_threshold_mm_s"],
            min_bout_duration_s=self.config["min_freezing_duration_s"],
        )
        total_duration = bout_metrics["total_duration_s"]
        pause_count = bout_metrics["pause_count"]
        pause_duration = bout_metrics["pause_duration_s"]

        metrics = {
            "configuration": dict(self.config),
            "pause_duration_s": pause_duration,
            "pause_count": pause_count,
            "pause_frequency_hz": (
                pause_count / total_duration if total_duration else 0.0
            ),
            "immobility_ratio": (
                pause_duration / total_duration if total_duration else 0.0
            ),
            "freezing_episodes": bout_metrics["pause_bouts"],
            "freezing_episode_count": pause_count,
            "source_bout_metrics": bout_metrics,
        }
        return AssayResult(
            assay_name=self.name,
            metrics=metrics,
            implemented_metrics=FREEZING_IMPLEMENTED_METRICS,
        )


__all__ = [
    "FREEZING_IMPLEMENTED_METRICS",
    "FreezingAssay",
]
