"""Turning metrics derived from heading time series."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def compute_turning_metrics(
    *,
    heading_rad: np.ndarray,
    timestep_s: float,
    turn_rate_threshold_rad_s: float,
    min_turn_duration_s: float = 0.0,
) -> dict[str, Any]:
    """Compute yaw rate, turn bouts, cumulative turning, and asymmetry."""

    headings = _as_heading_vector(heading_rad)
    timestep = _positive_float("timestep_s", timestep_s)
    threshold = _nonnegative_float(
        "turn_rate_threshold_rad_s", turn_rate_threshold_rad_s
    )
    min_duration = _nonnegative_float("min_turn_duration_s", min_turn_duration_s)

    unwrapped = np.unwrap(headings)
    yaw_delta = np.diff(unwrapped)
    yaw_rate = yaw_delta / timestep
    turn_mask = np.abs(yaw_rate) >= threshold
    turn_bouts = _turn_segments_to_bouts(
        turn_mask,
        yaw_delta=yaw_delta,
        yaw_rate=yaw_rate,
        timestep_s=timestep,
        min_duration_s=min_duration,
    )
    left_turning = float(np.sum(yaw_delta[yaw_delta > 0]))
    right_turning = float(abs(np.sum(yaw_delta[yaw_delta < 0])))
    total_directional = left_turning + right_turning

    return {
        "turn_rate_threshold_rad_s": _json_float(threshold),
        "min_turn_duration_s": _json_float(min_duration),
        "sample_count": int(headings.size),
        "step_count": int(yaw_delta.size),
        "heading_rad": _json_float_list(unwrapped),
        "yaw_rate_rad_s": _json_float_list(yaw_rate),
        "turn_angle_distribution_rad": _summary(yaw_delta),
        "turn_bouts": turn_bouts,
        "turn_bout_count": len(turn_bouts),
        "left_turn_bout_count": sum(1 for bout in turn_bouts if bout["direction"] == "left"),
        "right_turn_bout_count": sum(1 for bout in turn_bouts if bout["direction"] == "right"),
        "net_turn_angle_rad": _json_float(unwrapped[-1] - unwrapped[0]),
        "cumulative_turning_rad": _json_float(np.sum(np.abs(yaw_delta))),
        "left_turning_rad": _json_float(left_turning),
        "right_turning_rad": _json_float(right_turning),
        "left_right_asymmetry": _json_float(
            (left_turning - right_turning) / total_directional
            if total_directional > 0
            else 0.0
        ),
        "yaw_rate_summary_rad_s": _summary(yaw_rate),
    }


def compute_turning_metrics_from_quaternions(
    *,
    thorax_quaternions: np.ndarray,
    timestep_s: float,
    turn_rate_threshold_rad_s: float,
    min_turn_duration_s: float = 0.0,
) -> dict[str, Any]:
    """Compute turning metrics directly from thorax orientation quaternions."""

    quaternions = np.asarray(thorax_quaternions, dtype=float)
    if quaternions.ndim != 2 or quaternions.shape[1] != 4:
        raise ValueError("thorax_quaternions must have shape (n_samples, 4).")
    headings = np.array([_yaw_from_quaternion(quat) for quat in quaternions])
    return compute_turning_metrics(
        heading_rad=headings,
        timestep_s=timestep_s,
        turn_rate_threshold_rad_s=turn_rate_threshold_rad_s,
        min_turn_duration_s=min_turn_duration_s,
    )


def _turn_segments_to_bouts(
    mask: np.ndarray,
    *,
    yaw_delta: np.ndarray,
    yaw_rate: np.ndarray,
    timestep_s: float,
    min_duration_s: float,
) -> list[dict[str, Any]]:
    bouts = []
    start = None
    for index, active in enumerate(mask):
        if active and start is None:
            start = index
        if start is not None and (not active or index == len(mask) - 1):
            end = index if not active else index + 1
            duration = (end - start) * timestep_s
            if duration >= min_duration_s:
                angles = yaw_delta[start:end]
                rates = yaw_rate[start:end]
                net_angle = float(np.sum(angles))
                bouts.append(
                    {
                        "start_step": int(start),
                        "end_step_exclusive": int(end),
                        "start_time_s": _json_float(start * timestep_s),
                        "end_time_s": _json_float(end * timestep_s),
                        "duration_s": _json_float(duration),
                        "net_turn_angle_rad": _json_float(net_angle),
                        "absolute_turn_angle_rad": _json_float(np.sum(np.abs(angles))),
                        "mean_yaw_rate_rad_s": _json_float(np.mean(rates)),
                        "direction": "left" if net_angle >= 0 else "right",
                    }
                )
            start = None
    return bouts


def _as_heading_vector(value: np.ndarray) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 1:
        raise ValueError("heading_rad must be a one-dimensional array.")
    if array.size == 0:
        raise ValueError("heading_rad must contain at least one sample.")
    if not np.isfinite(array).all():
        raise ValueError("heading_rad must be finite.")
    return array


def _positive_float(name: str, value: Any) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be a positive finite number.")
    return result


def _nonnegative_float(name: str, value: Any) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be a non-negative finite number.")
    return result


def _summary(values: np.ndarray) -> dict[str, float | int | None]:
    array = np.asarray(values, dtype=float)
    return {
        "count": int(array.size),
        "min": _json_float(np.min(array)) if array.size else None,
        "max": _json_float(np.max(array)) if array.size else None,
        "mean": _json_float(np.mean(array)) if array.size else None,
        "absolute_mean": _json_float(np.mean(np.abs(array))) if array.size else None,
    }


def _json_float(value: Any) -> float | None:
    result = float(value)
    return result if math.isfinite(result) else None


def _json_float_list(values: np.ndarray) -> list[float | None]:
    return [_json_float(value) for value in np.asarray(values, dtype=float).ravel()]


def _yaw_from_quaternion(quat: np.ndarray) -> float:
    quat = np.asarray(quat, dtype=float)
    norm = np.linalg.norm(quat)
    if not np.isfinite(norm) or norm == 0:
        return math.nan
    w, x, y, z = quat / norm
    heading_x = 1 - 2 * (y * y + z * z)
    heading_y = 2 * (x * y + w * z)
    return math.atan2(heading_y, heading_x)


__all__ = [
    "compute_turning_metrics",
    "compute_turning_metrics_from_quaternions",
]
