"""G5 measurement extension over existing locomotion rollout arrays."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np

from drosophila_pd.metrics.bouts import compute_walking_bout_metrics
from drosophila_pd.metrics.open_field import (
    compute_open_field_metrics,
    open_field_unavailable,
)
from drosophila_pd.metrics.trajectory import compute_trajectory_timeseries
from drosophila_pd.metrics.turning import compute_turning_metrics


DEFAULT_MEASUREMENT_EXTENSION_CONFIG: dict[str, Any] = {
    "walking_bouts": {
        "speed_threshold_mm_s": 1.0,
        "min_bout_duration_s": 0.0,
    },
    "turning": {
        "turn_rate_threshold_rad_s": 0.5,
        "min_turn_duration_s": 0.0,
    },
    "open_field": {
        "enabled": False,
        "arena_center_xy_mm": [0.0, 0.0],
        "arena_size_mm": [100.0, 100.0],
        "center_fraction": 0.5,
        "border_width_mm": 10.0,
        "grid_bins": 8,
    },
}


def compute_extended_locomotion_metrics(
    *,
    thorax_positions: np.ndarray,
    thorax_quaternions: np.ndarray,
    timestep_s: float,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute G5 analysis metrics without running or mutating a simulation."""

    settings = _deep_merge(DEFAULT_MEASUREMENT_EXTENSION_CONFIG, config or {})
    trajectory = compute_trajectory_timeseries(
        thorax_positions=thorax_positions,
        thorax_quaternions=thorax_quaternions,
        timestep_s=timestep_s,
    )
    walking_bouts = compute_walking_bout_metrics(
        step_speed_mm_s=np.asarray(trajectory["step_speed_mm_s"], dtype=float),
        timestep_s=timestep_s,
        speed_threshold_mm_s=settings["walking_bouts"]["speed_threshold_mm_s"],
        min_bout_duration_s=settings["walking_bouts"]["min_bout_duration_s"],
    )
    turning = compute_turning_metrics(
        heading_rad=np.asarray(trajectory["heading_rad"], dtype=float),
        timestep_s=timestep_s,
        turn_rate_threshold_rad_s=settings["turning"]["turn_rate_threshold_rad_s"],
        min_turn_duration_s=settings["turning"]["min_turn_duration_s"],
    )

    if settings["open_field"].get("enabled"):
        open_field = compute_open_field_metrics(
            thorax_positions=thorax_positions,
            arena_center_xy_mm=settings["open_field"]["arena_center_xy_mm"],
            arena_size_mm=settings["open_field"]["arena_size_mm"],
            center_fraction=settings["open_field"]["center_fraction"],
            border_width_mm=settings["open_field"]["border_width_mm"],
            grid_bins=settings["open_field"]["grid_bins"],
        )
    else:
        open_field = open_field_unavailable("open_field.enabled is false")

    return {
        "measurement_extension_version": 1,
        "scientific_scope": (
            "G5 computes additional behavioral measurements from existing "
            "locomotion rollout arrays. It does not introduce perturbations, "
            "modify controllers, rerun simulations, or make biological "
            "Parkinson's disease claims."
        ),
        "configuration": settings,
        "trajectory": trajectory,
        "walking_bout_metrics": walking_bouts,
        "turning_metrics": turning,
        "open_field_metrics": open_field,
    }


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


__all__ = [
    "DEFAULT_MEASUREMENT_EXTENSION_CONFIG",
    "compute_extended_locomotion_metrics",
]
