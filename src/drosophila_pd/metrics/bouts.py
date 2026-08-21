"""Walking and pause bout segmentation for locomotion trajectories."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def compute_walking_bout_metrics(
    *,
    step_speed_mm_s: np.ndarray,
    timestep_s: float,
    speed_threshold_mm_s: float,
    min_bout_duration_s: float = 0.0,
) -> dict[str, Any]:
    """Segment step speeds into walking and pause bouts."""

    speeds = _as_speed_vector(step_speed_mm_s)
    timestep = _positive_float("timestep_s", timestep_s)
    threshold = _nonnegative_float("speed_threshold_mm_s", speed_threshold_mm_s)
    min_duration = _nonnegative_float("min_bout_duration_s", min_bout_duration_s)

    walking_mask = speeds > threshold
    walking_bouts = _segments_to_bouts(
        walking_mask,
        speeds=speeds,
        timestep_s=timestep,
        label="walking",
        min_duration_s=min_duration,
    )
    pause_bouts = _segments_to_bouts(
        ~walking_mask,
        speeds=speeds,
        timestep_s=timestep,
        label="pause",
        min_duration_s=min_duration,
    )
    total_duration = float(speeds.size * timestep)
    walking_duration = float(np.count_nonzero(walking_mask) * timestep)
    pause_duration = total_duration - walking_duration

    return {
        "speed_threshold_mm_s": _json_float(threshold),
        "min_bout_duration_s": _json_float(min_duration),
        "step_count": int(speeds.size),
        "total_duration_s": _json_float(total_duration),
        "walking_bouts": walking_bouts,
        "pause_bouts": pause_bouts,
        "bout_count": len(walking_bouts),
        "pause_count": len(pause_bouts),
        "walking_duration_s": _json_float(walking_duration),
        "pause_duration_s": _json_float(pause_duration),
        "walking_duty_cycle": _json_float(
            walking_duration / total_duration if total_duration > 0 else 0.0
        ),
    }


def compute_walking_bouts_from_positions(
    *,
    thorax_positions: np.ndarray,
    timestep_s: float,
    speed_threshold_mm_s: float,
    min_bout_duration_s: float = 0.0,
) -> dict[str, Any]:
    """Compute walking and pause bouts directly from thorax positions."""

    positions = np.asarray(thorax_positions, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("thorax_positions must have shape (n_samples, 3).")
    timestep = _positive_float("timestep_s", timestep_s)
    step_distances = np.linalg.norm(np.diff(positions[:, :2], axis=0), axis=1)
    return compute_walking_bout_metrics(
        step_speed_mm_s=step_distances / timestep,
        timestep_s=timestep,
        speed_threshold_mm_s=speed_threshold_mm_s,
        min_bout_duration_s=min_bout_duration_s,
    )


def _segments_to_bouts(
    mask: np.ndarray,
    *,
    speeds: np.ndarray,
    timestep_s: float,
    label: str,
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
                bout_speeds = speeds[start:end]
                bouts.append(
                    {
                        "type": label,
                        "start_step": int(start),
                        "end_step_exclusive": int(end),
                        "start_time_s": _json_float(start * timestep_s),
                        "end_time_s": _json_float(end * timestep_s),
                        "duration_s": _json_float(duration),
                        "mean_speed_mm_s": _json_float(np.mean(bout_speeds)),
                        "distance_mm": _json_float(np.sum(bout_speeds) * timestep_s),
                    }
                )
            start = None
    return bouts


def _as_speed_vector(value: np.ndarray) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 1:
        raise ValueError("step_speed_mm_s must be a one-dimensional array.")
    if not np.isfinite(array).all():
        raise ValueError("step_speed_mm_s must be finite.")
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


def _json_float(value: Any) -> float | None:
    result = float(value)
    return result if math.isfinite(result) else None


__all__ = [
    "compute_walking_bout_metrics",
    "compute_walking_bouts_from_positions",
]
