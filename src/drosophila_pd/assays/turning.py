"""Turning assay over existing heading outputs."""

from __future__ import annotations

from typing import Any

import numpy as np

from drosophila_pd.assays.base import (
    IMPLEMENTED,
    AssayMetricSpec,
    AssayResult,
    BehavioralAssay,
    RolloutAssayInput,
)
from drosophila_pd.metrics.trajectory import compute_trajectory_timeseries
from drosophila_pd.metrics.turning import compute_turning_metrics


TURNING_IMPLEMENTED_METRICS = (
    AssayMetricSpec(
        name="yaw_rate_distribution",
        status=IMPLEMENTED,
        description="Yaw-rate time series and summary statistics.",
        required_inputs=("thorax_quaternions", "timestep_s"),
    ),
    AssayMetricSpec(
        name="turn_bout_detection",
        status=IMPLEMENTED,
        description="Contiguous periods exceeding the yaw-rate threshold.",
        required_inputs=("thorax_quaternions", "timestep_s"),
    ),
    AssayMetricSpec(
        name="cumulative_turning",
        status=IMPLEMENTED,
        description="Sum of absolute yaw-angle changes.",
        required_inputs=("thorax_quaternions", "timestep_s"),
    ),
    AssayMetricSpec(
        name="left_right_bias",
        status=IMPLEMENTED,
        description="Signed asymmetry of left versus right turning.",
        required_inputs=("thorax_quaternions", "timestep_s"),
    ),
    AssayMetricSpec(
        name="turn_angle_histogram",
        status=IMPLEMENTED,
        description="Histogram of per-step yaw-angle changes.",
        required_inputs=("thorax_quaternions", "timestep_s"),
    ),
)


class TurningAssay(BehavioralAssay):
    """Compute turning behavior from rollout orientation arrays."""

    name = "turning"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = {
            "turn_rate_threshold_rad_s": 0.5,
            "min_turn_duration_s": 0.0,
            "turn_angle_histogram_bins": 16,
            **(config or {}),
        }

    def specification(self) -> dict[str, Any]:
        return {
            "assay_name": self.name,
            "implemented_metrics": [
                metric.as_dict() for metric in TURNING_IMPLEMENTED_METRICS
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
        heading = np.asarray(trajectory["heading_rad"], dtype=float)
        turning = compute_turning_metrics(
            heading_rad=heading,
            timestep_s=timestep,
            turn_rate_threshold_rad_s=self.config["turn_rate_threshold_rad_s"],
            min_turn_duration_s=self.config["min_turn_duration_s"],
        )
        yaw_delta = np.diff(np.unwrap(heading))
        counts, edges = np.histogram(
            yaw_delta,
            bins=int(self.config["turn_angle_histogram_bins"]),
        )

        metrics = {
            "configuration": dict(self.config),
            "yaw_rate_rad_s": turning["yaw_rate_rad_s"],
            "yaw_rate_summary_rad_s": turning["yaw_rate_summary_rad_s"],
            "turn_bouts": turning["turn_bouts"],
            "turn_bout_count": turning["turn_bout_count"],
            "cumulative_turning_rad": turning["cumulative_turning_rad"],
            "net_turn_angle_rad": turning["net_turn_angle_rad"],
            "left_turning_rad": turning["left_turning_rad"],
            "right_turning_rad": turning["right_turning_rad"],
            "left_right_bias": turning["left_right_asymmetry"],
            "turn_angle_distribution_rad": turning["turn_angle_distribution_rad"],
            "turn_angle_histogram": {
                "counts": [int(value) for value in counts],
                "bin_edges_rad": [float(value) for value in edges],
            },
        }
        return AssayResult(
            assay_name=self.name,
            metrics=metrics,
            implemented_metrics=TURNING_IMPLEMENTED_METRICS,
        )


__all__ = [
    "TURNING_IMPLEMENTED_METRICS",
    "TurningAssay",
]
