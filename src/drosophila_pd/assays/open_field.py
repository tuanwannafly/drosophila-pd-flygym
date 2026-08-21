"""Open-field assay over existing trajectory outputs."""

from __future__ import annotations

from typing import Any

from drosophila_pd.assays.base import (
    IMPLEMENTED,
    AssayMetricSpec,
    AssayResult,
    BehavioralAssay,
    RolloutAssayInput,
)
from drosophila_pd.metrics.open_field import compute_open_field_metrics
from drosophila_pd.metrics.trajectory import compute_trajectory_timeseries


OPEN_FIELD_IMPLEMENTED_METRICS = (
    AssayMetricSpec(
        name="trajectory_visualization",
        status=IMPLEMENTED,
        description="CSV/plot-ready x-y trajectory trace and bounds.",
        required_inputs=("thorax_positions", "thorax_quaternions", "timestep_s"),
    ),
    AssayMetricSpec(
        name="center_occupancy",
        status=IMPLEMENTED,
        description="Fraction of samples inside the declared center region.",
        required_inputs=("thorax_positions", "arena geometry"),
    ),
    AssayMetricSpec(
        name="border_occupancy",
        status=IMPLEMENTED,
        description="Fraction of samples inside the declared border region.",
        required_inputs=("thorax_positions", "arena geometry"),
    ),
    AssayMetricSpec(
        name="exploration_index",
        status=IMPLEMENTED,
        description="Fraction of virtual grid bins visited inside the arena.",
        required_inputs=("thorax_positions", "arena geometry"),
    ),
    AssayMetricSpec(
        name="radial_distance_statistics",
        status=IMPLEMENTED,
        description="Summary of distance from the declared arena center.",
        required_inputs=("thorax_positions", "arena geometry"),
    ),
)


class OpenFieldAssay(BehavioralAssay):
    """Compute open-field-style metrics from a flat-ground trajectory."""

    name = "open_field"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = {
            "arena_center_xy_mm": [0.0, 0.0],
            "arena_size_mm": [100.0, 100.0],
            "center_fraction": 0.5,
            "border_width_mm": 10.0,
            "grid_bins": 8,
            **(config or {}),
        }

    def specification(self) -> dict[str, Any]:
        return {
            "assay_name": self.name,
            "implemented_metrics": [
                metric.as_dict() for metric in OPEN_FIELD_IMPLEMENTED_METRICS
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
        open_field = compute_open_field_metrics(
            thorax_positions=positions,
            arena_center_xy_mm=self.config["arena_center_xy_mm"],
            arena_size_mm=self.config["arena_size_mm"],
            center_fraction=self.config["center_fraction"],
            border_width_mm=self.config["border_width_mm"],
            grid_bins=self.config["grid_bins"],
        )

        x_values = trajectory["x_mm"]
        y_values = trajectory["y_mm"]
        metrics = {
            "configuration": dict(self.config),
            "trajectory_visualization": {
                "sample_count": trajectory["sample_count"],
                "time_s": trajectory["time_s"],
                "x_mm": x_values,
                "y_mm": y_values,
                "heading_rad": trajectory["heading_rad"],
                "bounds_mm": {
                    "x_min": min(x_values),
                    "x_max": max(x_values),
                    "y_min": min(y_values),
                    "y_max": max(y_values),
                },
                "path_length_mm": trajectory["summary"]["path_length_mm"],
            },
            "center_occupancy": open_field["center_occupancy"],
            "border_occupancy": open_field["border_occupancy"],
            "exploration_index": open_field["exploration_index"],
            "radial_distance_mm": open_field["radial_distance_mm"],
            "in_arena_fraction": open_field["in_arena_fraction"],
        }
        return AssayResult(
            assay_name=self.name,
            metrics=metrics,
            implemented_metrics=OPEN_FIELD_IMPLEMENTED_METRICS,
        )


__all__ = [
    "OPEN_FIELD_IMPLEMENTED_METRICS",
    "OpenFieldAssay",
]
