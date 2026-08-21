"""Trajectory time-series utilities for locomotion rollouts."""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

import numpy as np


TRAJECTORY_CSV_COLUMNS = [
    "sample_index",
    "time_s",
    "x_mm",
    "y_mm",
    "z_mm",
    "heading_rad",
    "instantaneous_speed_mm_s",
    "cumulative_distance_mm",
]


def compute_trajectory_timeseries(
    *,
    thorax_positions: np.ndarray,
    thorax_quaternions: np.ndarray,
    timestep_s: float,
) -> dict[str, Any]:
    """Compute per-sample trajectory data from canonical rollout arrays."""

    positions = _as_positions(thorax_positions)
    quaternions = _as_quaternions(thorax_quaternions)
    timestep = _positive_float("timestep_s", timestep_s)
    if positions.shape[0] != quaternions.shape[0]:
        raise ValueError("position and quaternion sample counts must match.")

    sample_count = int(positions.shape[0])
    segment_vectors = np.diff(positions[:, :2], axis=0)
    segment_distances = np.linalg.norm(segment_vectors, axis=1)
    segment_speeds = segment_distances / timestep

    instantaneous_speed = np.zeros(sample_count, dtype=float)
    if sample_count > 1:
        instantaneous_speed[1:] = segment_speeds

    cumulative_distance = np.zeros(sample_count, dtype=float)
    if sample_count > 1:
        cumulative_distance[1:] = np.cumsum(segment_distances)

    headings = np.unwrap(
        np.array([_yaw_from_quaternion(quat) for quat in quaternions], dtype=float)
    )
    times = np.arange(sample_count, dtype=float) * timestep

    return {
        "sample_count": sample_count,
        "timestep_s": _json_float(timestep),
        "time_s": _json_float_list(times),
        "x_mm": _json_float_list(positions[:, 0]),
        "y_mm": _json_float_list(positions[:, 1]),
        "z_mm": _json_float_list(positions[:, 2]),
        "heading_rad": _json_float_list(headings),
        "instantaneous_speed_mm_s": _json_float_list(instantaneous_speed),
        "step_speed_mm_s": _json_float_list(segment_speeds),
        "cumulative_distance_mm": _json_float_list(cumulative_distance),
        "summary": {
            "duration_s": _json_float((sample_count - 1) * timestep),
            "path_length_mm": _json_float(cumulative_distance[-1]),
            "final_x_mm": _json_float(positions[-1, 0]),
            "final_y_mm": _json_float(positions[-1, 1]),
            "final_z_mm": _json_float(positions[-1, 2]),
            "mean_step_speed_mm_s": _json_float(
                np.mean(segment_speeds) if segment_speeds.size else 0.0
            ),
            "max_step_speed_mm_s": _json_float(
                np.max(segment_speeds) if segment_speeds.size else 0.0
            ),
        },
    }


def trajectory_csv_rows(trajectory: dict[str, Any]) -> list[dict[str, Any]]:
    """Return CSV-ready rows from a trajectory time-series mapping."""

    rows = []
    for index in range(int(trajectory["sample_count"])):
        rows.append(
            {
                "sample_index": index,
                "time_s": trajectory["time_s"][index],
                "x_mm": trajectory["x_mm"][index],
                "y_mm": trajectory["y_mm"][index],
                "z_mm": trajectory["z_mm"][index],
                "heading_rad": trajectory["heading_rad"][index],
                "instantaneous_speed_mm_s": trajectory[
                    "instantaneous_speed_mm_s"
                ][index],
                "cumulative_distance_mm": trajectory["cumulative_distance_mm"][
                    index
                ],
            }
        )
    return rows


def write_trajectory_csv(
    trajectory: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Write trajectory rows to CSV and return the path."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRAJECTORY_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(trajectory_csv_rows(trajectory))
    return path


def _as_positions(value: np.ndarray) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[1] != 3:
        raise ValueError("thorax_positions must have shape (n_samples, 3).")
    if array.shape[0] == 0:
        raise ValueError("thorax_positions must contain at least one sample.")
    return array


def _as_quaternions(value: np.ndarray) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[1] != 4:
        raise ValueError("thorax_quaternions must have shape (n_samples, 4).")
    if array.shape[0] == 0:
        raise ValueError("thorax_quaternions must contain at least one sample.")
    return array


def _positive_float(name: str, value: Any) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be a positive finite number.")
    return result


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
    "TRAJECTORY_CSV_COLUMNS",
    "compute_trajectory_timeseries",
    "trajectory_csv_rows",
    "write_trajectory_csv",
]
