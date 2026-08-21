"""Complete v2 behavioral measurements computed from rollout arrays."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import numpy as np

from drosophila_pd.assays.base import RolloutAssayInput
from drosophila_pd.assays.suite import run_behavioral_assay_suite
from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.metrics.bouts import compute_walking_bout_metrics
from drosophila_pd.metrics.open_field import compute_open_field_metrics
from drosophila_pd.metrics.trajectory import compute_trajectory_timeseries
from drosophila_pd.metrics.turning import compute_turning_metrics


DEFAULT_BEHAVIOR_MEASUREMENT_CONFIG: dict[str, Any] = {
    "walking": {
        "speed_threshold_mm_s": 1.0,
        "min_bout_duration_s": 0.0,
    },
    "freezing": {
        "immobility_speed_threshold_mm_s": 0.5,
        "min_freezing_duration_s": 0.0,
    },
    "turning": {
        "turn_rate_threshold_rad_s": 0.5,
        "min_turn_duration_s": 0.0,
        "turn_angle_histogram_bins": 16,
    },
    "open_field": {
        "enabled": True,
        "arena_center_xy_mm": [0.0, 0.0],
        "arena_size_mm": [100.0, 100.0],
        "center_fraction": 0.5,
        "border_width_mm": 10.0,
        "grid_bins": 8,
    },
}


def measure_rollout_behavior(
    rollout: RolloutData,
    *,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute the canonical v2 behavioral platform metrics."""

    settings = _deep_merge(DEFAULT_BEHAVIOR_MEASUREMENT_CONFIG, config or {})
    positions = rollout.positions_array()
    quaternions = rollout.quaternions_array()
    timestep = rollout.timestep()
    sample_count = rollout.sample_count()

    trajectory = compute_trajectory_timeseries(
        thorax_positions=positions,
        thorax_quaternions=quaternions,
        timestep_s=timestep,
    )
    walking = compute_walking_bout_metrics(
        step_speed_mm_s=np.asarray(trajectory["step_speed_mm_s"], dtype=float),
        timestep_s=timestep,
        speed_threshold_mm_s=settings["walking"]["speed_threshold_mm_s"],
        min_bout_duration_s=settings["walking"]["min_bout_duration_s"],
    )
    freezing = compute_walking_bout_metrics(
        step_speed_mm_s=np.asarray(trajectory["step_speed_mm_s"], dtype=float),
        timestep_s=timestep,
        speed_threshold_mm_s=settings["freezing"]["immobility_speed_threshold_mm_s"],
        min_bout_duration_s=settings["freezing"]["min_freezing_duration_s"],
    )
    heading = np.asarray(trajectory["heading_rad"], dtype=float)
    turning = compute_turning_metrics(
        heading_rad=heading,
        timestep_s=timestep,
        turn_rate_threshold_rad_s=settings["turning"]["turn_rate_threshold_rad_s"],
        min_turn_duration_s=settings["turning"]["min_turn_duration_s"],
    )
    path_geometry = _path_geometry(
        positions=positions,
        heading_rad=heading,
        step_speed_mm_s=np.asarray(trajectory["step_speed_mm_s"], dtype=float),
    )
    open_field = (
        compute_open_field_metrics(
            thorax_positions=positions,
            arena_center_xy_mm=settings["open_field"]["arena_center_xy_mm"],
            arena_size_mm=settings["open_field"]["arena_size_mm"],
            center_fraction=settings["open_field"]["center_fraction"],
            border_width_mm=settings["open_field"]["border_width_mm"],
            grid_bins=settings["open_field"]["grid_bins"],
        )
        if settings["open_field"].get("enabled", True)
        else {"available": False, "reason": "open_field.enabled is false"}
    )
    adhesion = _adhesion_summary(rollout.adhesion_arrays())
    joints = _joint_summary(rollout.joint_arrays())
    com = _com_summary(rollout.com_array(), timestep_s=timestep)
    assays = run_behavioral_assay_suite(
        rollout=RolloutAssayInput(
            thorax_positions=positions,
            thorax_quaternions=quaternions,
            timestep_s=timestep,
            adhesion_outputs=rollout.adhesion_arrays(),
            metadata=rollout.metadata,
        ),
        config={
            "open_field": settings["open_field"],
            "freezing": settings["freezing"],
            "turning": settings["turning"],
            "gait": {"enabled": True},
        },
    )

    return {
        "behavior_platform_version": 2,
        "scientific_scope": (
            "Rollout post-processing only. The v2 behavioral platform does not "
            "run simulations, introduce perturbations, tune candidate "
            "parameters, or make biological Parkinson's disease claims."
        ),
        "rollout": rollout.as_metadata(),
        "configuration": settings,
        "time_s": _json_float_list(rollout.time_s()),
        "trajectory": trajectory,
        "walking_bouts": walking["walking_bouts"],
        "pause_bouts": walking["pause_bouts"],
        "walking_summary": {
            "bout_count": walking["bout_count"],
            "pause_count": walking["pause_count"],
            "walking_duration_s": walking["walking_duration_s"],
            "pause_duration_s": walking["pause_duration_s"],
            "walking_duty_cycle": walking["walking_duty_cycle"],
        },
        "freezing": {
            "freezing_episode_count": freezing["pause_count"],
            "freezing_episodes": freezing["pause_bouts"],
            "freezing_duration_s": freezing["pause_duration_s"],
            "immobility_ratio": (
                freezing["pause_duration_s"] / freezing["total_duration_s"]
                if freezing["total_duration_s"]
                else 0.0
            ),
            "configuration": settings["freezing"],
        },
        "heading_rad": trajectory["heading_rad"],
        "yaw_rad": trajectory["heading_rad"],
        "yaw_rate_rad_s": turning["yaw_rate_rad_s"],
        "turn_bouts": turning["turn_bouts"],
        "turning_summary": {
            "turn_bout_count": turning["turn_bout_count"],
            "cumulative_turning_rad": turning["cumulative_turning_rad"],
            "left_turning_rad": turning["left_turning_rad"],
            "right_turning_rad": turning["right_turning_rad"],
            "left_right_bias": turning["left_right_asymmetry"],
            "yaw_rate_summary_rad_s": turning["yaw_rate_summary_rad_s"],
            "turn_angle_distribution_rad": turning["turn_angle_distribution_rad"],
        },
        "path_geometry": path_geometry,
        "exploration_metrics": open_field,
        "adhesion_summary": adhesion,
        "joint_summary": joints,
        "com_summary": com,
        "assay_suite": assays,
        "all_metrics_finite": _all_numbers_finite(
            {
                "trajectory": trajectory,
                "walking": walking,
                "freezing": freezing,
                "turning": turning,
                "path_geometry": path_geometry,
                "open_field": open_field,
                "adhesion": adhesion,
                "joints": joints,
                "com": com,
            }
        ),
    }


def _path_geometry(
    *,
    positions: np.ndarray,
    heading_rad: np.ndarray,
    step_speed_mm_s: np.ndarray,
) -> dict[str, Any]:
    xy = positions[:, :2]
    deltas = np.diff(xy, axis=0)
    step_distance = np.linalg.norm(deltas, axis=1)
    yaw_delta = np.diff(np.unwrap(heading_rad))
    curvature = np.zeros_like(yaw_delta, dtype=float)
    moving = step_distance > 1e-12
    curvature[moving] = yaw_delta[moving] / step_distance[moving]
    path_length = float(np.sum(step_distance))
    displacement = float(np.linalg.norm(xy[-1] - xy[0]))
    tortuosity = path_length / displacement if displacement > 1e-12 else None
    return {
        "curvature_rad_per_mm": _json_float_list(curvature),
        "curvature_summary_rad_per_mm": _summary(curvature),
        "path_length_mm": _json_float(path_length),
        "planar_displacement_mm": _json_float(displacement),
        "tortuosity": _json_float(tortuosity) if tortuosity is not None else None,
        "mean_instantaneous_speed_mm_s": _json_float(np.mean(step_speed_mm_s))
        if step_speed_mm_s.size
        else 0.0,
    }


def _adhesion_summary(values: dict[str, np.ndarray]) -> dict[str, Any]:
    if not values:
        return {"available": False, "duty_factor_by_leg": {}, "transition_count_by_leg": {}}
    duty: dict[str, float] = {}
    transitions: dict[str, int] = {}
    for leg, array in values.items():
        active = np.asarray(array, dtype=float).ravel() > 0.5
        duty[leg] = _json_float(np.count_nonzero(active) / active.size)
        transitions[leg] = int(np.count_nonzero(np.diff(active)))
    return {
        "available": True,
        "duty_factor_by_leg": duty,
        "transition_count_by_leg": transitions,
    }


def _joint_summary(values: dict[str, np.ndarray]) -> dict[str, Any]:
    return {
        "available": bool(values),
        "joint_count": len(values),
        "joints": {
            name: {
                "sample_count": int(array.shape[0]),
                "mean": _json_float(np.mean(array)),
                "absolute_mean": _json_float(np.mean(np.abs(array))),
                "min": _json_float(np.min(array)),
                "max": _json_float(np.max(array)),
            }
            for name, array in values.items()
        },
    }


def _com_summary(value: np.ndarray | None, *, timestep_s: float) -> dict[str, Any]:
    if value is None:
        return {"available": False}
    deltas = np.diff(value[:, :2], axis=0)
    speed = np.linalg.norm(deltas, axis=1) / timestep_s if deltas.size else np.array([])
    return {
        "available": True,
        "sample_count": int(value.shape[0]),
        "x_mm": _json_float_list(value[:, 0]),
        "y_mm": _json_float_list(value[:, 1]),
        "z_mm": _json_float_list(value[:, 2]),
        "speed_summary_mm_s": _summary(speed),
    }


def _summary(values: np.ndarray) -> dict[str, float | int | None]:
    array = np.asarray(values, dtype=float)
    return {
        "count": int(array.size),
        "min": _json_float(np.min(array)) if array.size else None,
        "max": _json_float(np.max(array)) if array.size else None,
        "mean": _json_float(np.mean(array)) if array.size else None,
        "absolute_mean": _json_float(np.mean(np.abs(array))) if array.size else None,
    }


def _all_numbers_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_all_numbers_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_all_numbers_finite(item) for item in value)
    if isinstance(value, (str, bool)) or value is None:
        return True
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return True


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _json_float(value: Any) -> float | None:
    result = float(value)
    return result if np.isfinite(result) else None


def _json_float_list(values: np.ndarray) -> list[float | None]:
    return [_json_float(value) for value in np.asarray(values, dtype=float).ravel()]


__all__ = ["DEFAULT_BEHAVIOR_MEASUREMENT_CONFIG", "measure_rollout_behavior"]
