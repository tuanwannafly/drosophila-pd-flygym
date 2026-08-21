"""Optional virtual open-field metrics for flat-ground trajectories."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def compute_open_field_metrics(
    *,
    thorax_positions: np.ndarray,
    arena_center_xy_mm: tuple[float, float] | list[float],
    arena_size_mm: tuple[float, float] | list[float],
    center_fraction: float,
    border_width_mm: float,
    grid_bins: int = 8,
) -> dict[str, Any]:
    """Compute occupancy metrics in a virtual rectangular arena."""

    positions = np.asarray(thorax_positions, dtype=float)
    if positions.ndim != 2 or positions.shape[1] != 3:
        raise ValueError("thorax_positions must have shape (n_samples, 3).")
    if positions.shape[0] == 0:
        raise ValueError("thorax_positions must contain at least one sample.")
    center = _xy_vector("arena_center_xy_mm", arena_center_xy_mm)
    size = _positive_xy_vector("arena_size_mm", arena_size_mm)
    center_fraction_value = _bounded_fraction("center_fraction", center_fraction)
    border_width = _nonnegative_float("border_width_mm", border_width_mm)
    if border_width * 2 > min(size):
        raise ValueError("border_width_mm is too large for arena_size_mm.")
    bins = int(grid_bins)
    if bins <= 0:
        raise ValueError("grid_bins must be a positive integer.")

    xy = positions[:, :2] - center
    half_size = size / 2.0
    in_arena = (np.abs(xy[:, 0]) <= half_size[0]) & (
        np.abs(xy[:, 1]) <= half_size[1]
    )
    center_half_size = half_size * center_fraction_value
    in_center = (np.abs(xy[:, 0]) <= center_half_size[0]) & (
        np.abs(xy[:, 1]) <= center_half_size[1]
    )
    in_border = in_arena & (
        (half_size[0] - np.abs(xy[:, 0]) <= border_width)
        | (half_size[1] - np.abs(xy[:, 1]) <= border_width)
    )
    radial_distance = np.linalg.norm(xy, axis=1)

    occupied_bins = _occupied_grid_fraction(
        xy[in_arena],
        half_size=half_size,
        grid_bins=bins,
    )

    sample_count = int(positions.shape[0])
    return {
        "available": True,
        "arena_center_xy_mm": _json_float_list(center),
        "arena_size_mm": _json_float_list(size),
        "center_fraction": _json_float(center_fraction_value),
        "border_width_mm": _json_float(border_width),
        "grid_bins": bins,
        "sample_count": sample_count,
        "in_arena_fraction": _json_float(np.count_nonzero(in_arena) / sample_count),
        "center_occupancy": _json_float(np.count_nonzero(in_center) / sample_count),
        "border_occupancy": _json_float(np.count_nonzero(in_border) / sample_count),
        "radial_distance_mm": _summary(radial_distance),
        "exploration_index": _json_float(occupied_bins),
    }


def open_field_unavailable(reason: str) -> dict[str, Any]:
    """Return an explicit unavailable record for optional open-field metrics."""

    return {
        "available": False,
        "reason": reason,
        "center_occupancy": None,
        "border_occupancy": None,
        "radial_distance_mm": None,
        "exploration_index": None,
    }


def _occupied_grid_fraction(
    xy: np.ndarray,
    *,
    half_size: np.ndarray,
    grid_bins: int,
) -> float:
    if xy.size == 0:
        return 0.0
    normalized = (xy + half_size) / (2.0 * half_size)
    clipped = np.clip(normalized, 0.0, np.nextafter(1.0, 0.0))
    indices = np.floor(clipped * grid_bins).astype(int)
    occupied = {tuple(index) for index in indices}
    return len(occupied) / float(grid_bins * grid_bins)


def _xy_vector(name: str, value: tuple[float, float] | list[float]) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.shape != (2,) or not np.isfinite(array).all():
        raise ValueError(f"{name} must be a finite two-value vector.")
    return array


def _positive_xy_vector(name: str, value: tuple[float, float] | list[float]) -> np.ndarray:
    array = _xy_vector(name, value)
    if np.any(array <= 0):
        raise ValueError(f"{name} values must be positive.")
    return array


def _bounded_fraction(name: str, value: Any) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0 or result > 1:
        raise ValueError(f"{name} must be in the interval (0, 1].")
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
        "final": _json_float(array[-1]) if array.size else None,
    }


def _json_float(value: Any) -> float | None:
    result = float(value)
    return result if math.isfinite(result) else None


def _json_float_list(values: np.ndarray) -> list[float | None]:
    return [_json_float(value) for value in np.asarray(values, dtype=float).ravel()]


__all__ = [
    "compute_open_field_metrics",
    "open_field_unavailable",
]
