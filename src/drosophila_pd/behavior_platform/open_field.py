"""Reusable open-field arena analysis for Session07."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from drosophila_pd.behavior_platform.data_model import Arena, ArenaZone
from drosophila_pd.behavior_platform.rollout import RolloutData


def analyze_open_field(
    rollout: RolloutData,
    arena: Arena,
    *,
    grid_bins: int = 12,
) -> dict[str, Any]:
    """Compute open-field occupancy and exploration metrics from a rollout."""

    positions = rollout.positions_array()
    timestep = rollout.timestep()
    bins = _positive_int("grid_bins", grid_bins)
    xy = positions[:, :2]
    centered = xy - np.asarray(arena.center_xy_mm, dtype=float)
    in_arena = _arena_mask(centered, arena)
    center = _center_mask(centered, arena)
    border = _border_mask(centered, arena)
    radial_distance = np.linalg.norm(centered, axis=1)
    heatmap, x_edges, y_edges = _occupancy_histogram(centered, arena, bins=bins)
    occupied_bins = int(np.count_nonzero(heatmap))
    zone_labels = _zone_labels(centered, arena, center=center, border=border, in_arena=in_arena)
    transition = _zone_transition_matrix(zone_labels)
    step_distance = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    heading = np.unwrap(np.arctan2(np.diff(xy[:, 1]), np.diff(xy[:, 0])))
    curvature = _path_curvature(step_distance, heading)
    path_length = float(np.sum(step_distance))
    displacement = float(np.linalg.norm(xy[-1] - xy[0]))

    return {
        "open_field_version": 2,
        "scientific_scope": (
            "Open-field metrics are computational descriptors of simulated "
            "trajectory arrays only; they are not biological validation."
        ),
        "rollout": rollout.as_metadata(),
        "arena": arena.as_dict(),
        "sample_count": int(positions.shape[0]),
        "positions_xy_mm": xy.tolist(),
        "center_occupancy": _json_float(np.mean(center)),
        "border_occupancy": _json_float(np.mean(border)),
        "exploration_index": _json_float(occupied_bins / float(bins * bins)),
        "radial_distance_mm": _summary(radial_distance),
        "radial_distance_timeseries_mm": _json_float_list(radial_distance),
        "heat_map": {
            "grid_bins": bins,
            "x_edges_mm": _json_float_list(x_edges),
            "y_edges_mm": _json_float_list(y_edges),
            "counts": heatmap.astype(int).tolist(),
        },
        "occupancy_histogram": {
            "counts": heatmap.astype(int).tolist(),
            "probability": _safe_probability(heatmap).tolist(),
        },
        "transition_probability_matrix": transition["probability_matrix"],
        "zone_transition_graph": transition["graph"],
        "zone_labels": zone_labels,
        "exploration_entropy_bits": _json_float(_entropy(heatmap.ravel())),
        "coverage_ratio": _json_float(occupied_bins / float(bins * bins)),
        "revisit_frequency_hz": _json_float(_revisit_count(heatmap) / _duration_s(positions.shape[0], timestep)),
        "path_tortuosity": _json_float(path_length / displacement) if displacement > 1e-12 else None,
        "path_curvature_rad_per_mm": _json_float_list(curvature),
        "path_curvature_summary_rad_per_mm": _summary(curvature),
        "dwell_time_s_by_zone": _dwell_time(zone_labels, timestep),
        "custom_zone_occupancy": _custom_zone_occupancy(centered, arena.zones),
        "all_metrics_finite": _all_numbers_finite(
            {
                "center": float(np.mean(center)),
                "border": float(np.mean(border)),
                "radial": radial_distance,
                "heatmap": heatmap,
                "curvature": curvature,
            }
        ),
    }


def export_open_field_report(
    report: Mapping[str, Any],
    output_dir: str | Path,
    *,
    formats: Sequence[str] = ("json", "csv"),
) -> dict[str, Path]:
    """Export an open-field report as JSON and/or CSV tables."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    normalized = tuple(fmt.lower() for fmt in formats)
    unsupported = sorted(set(normalized) - {"json", "csv"})
    if unsupported:
        raise ValueError(f"unsupported open-field export formats: {unsupported}")
    files: dict[str, Path] = {}
    if "json" in normalized:
        path = output / "open_field_report.json"
        path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
        files["json"] = path
    if "csv" in normalized:
        radial = output / "radial_distance.csv"
        with radial.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["sample_index", "radial_distance_mm", "zone"])
            writer.writeheader()
            for index, (distance, zone) in enumerate(
                zip(report["radial_distance_timeseries_mm"], report["zone_labels"])
            ):
                writer.writerow(
                    {
                        "sample_index": index,
                        "radial_distance_mm": distance,
                        "zone": zone,
                    }
                )
        files["radial_csv"] = radial
    return files


def _arena_mask(centered_xy: np.ndarray, arena: Arena) -> np.ndarray:
    if arena.shape == "circle":
        radius = _positive_float("radius_mm", arena.radius_mm)
        return np.linalg.norm(centered_xy, axis=1) <= radius
    if arena.shape == "rectangle":
        size = _size(arena)
        return (np.abs(centered_xy[:, 0]) <= size[0] / 2) & (
            np.abs(centered_xy[:, 1]) <= size[1] / 2
        )
    raise ValueError(f"unsupported arena shape: {arena.shape}")


def _center_mask(centered_xy: np.ndarray, arena: Arena) -> np.ndarray:
    fraction = _bounded_fraction("center_fraction", arena.center_fraction)
    if arena.shape == "circle":
        return np.linalg.norm(centered_xy, axis=1) <= _positive_float("radius_mm", arena.radius_mm) * fraction
    size = _size(arena) * fraction
    return (np.abs(centered_xy[:, 0]) <= size[0] / 2) & (
        np.abs(centered_xy[:, 1]) <= size[1] / 2
    )


def _border_mask(centered_xy: np.ndarray, arena: Arena) -> np.ndarray:
    border = _nonnegative_float("border_width_mm", arena.border_width_mm)
    if arena.shape == "circle":
        radius = _positive_float("radius_mm", arena.radius_mm)
        distance = np.linalg.norm(centered_xy, axis=1)
        return (distance <= radius) & (distance >= max(0.0, radius - border))
    size = _size(arena)
    half = size / 2
    in_rect = _arena_mask(centered_xy, arena)
    return in_rect & (
        (half[0] - np.abs(centered_xy[:, 0]) <= border)
        | (half[1] - np.abs(centered_xy[:, 1]) <= border)
    )


def _zone_labels(
    centered_xy: np.ndarray,
    arena: Arena,
    *,
    center: np.ndarray,
    border: np.ndarray,
    in_arena: np.ndarray,
) -> list[str]:
    labels = []
    custom_masks = [(zone.name, _zone_mask(centered_xy, zone)) for zone in arena.zones]
    for index in range(centered_xy.shape[0]):
        custom = next((name for name, mask in custom_masks if mask[index]), None)
        if custom is not None:
            labels.append(custom)
        elif not in_arena[index]:
            labels.append("outside")
        elif center[index]:
            labels.append("center")
        elif border[index]:
            labels.append("border")
        else:
            labels.append("arena")
    return labels


def _zone_mask(centered_xy: np.ndarray, zone: ArenaZone) -> np.ndarray:
    shifted = centered_xy - np.asarray(zone.center_xy_mm, dtype=float)
    if zone.shape == "circle":
        return np.linalg.norm(shifted, axis=1) <= _positive_float("zone.radius_mm", zone.radius_mm)
    if zone.shape == "rectangle":
        size = np.asarray(zone.size_xy_mm, dtype=float)
        if size.shape != (2,) or np.any(size <= 0):
            raise ValueError("rectangular ArenaZone requires positive size_xy_mm.")
        return (np.abs(shifted[:, 0]) <= size[0] / 2) & (np.abs(shifted[:, 1]) <= size[1] / 2)
    raise ValueError(f"unsupported zone shape: {zone.shape}")


def _custom_zone_occupancy(centered_xy: np.ndarray, zones: Sequence[ArenaZone]) -> dict[str, float | None]:
    return {
        zone.name: _json_float(np.mean(_zone_mask(centered_xy, zone)))
        for zone in zones
    }


def _occupancy_histogram(centered_xy: np.ndarray, arena: Arena, *, bins: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if arena.shape == "circle":
        radius = _positive_float("radius_mm", arena.radius_mm)
        ranges = [[-radius, radius], [-radius, radius]]
    else:
        size = _size(arena)
        ranges = [[-size[0] / 2, size[0] / 2], [-size[1] / 2, size[1] / 2]]
    return np.histogram2d(centered_xy[:, 0], centered_xy[:, 1], bins=bins, range=ranges)


def _zone_transition_matrix(labels: Sequence[str]) -> dict[str, Any]:
    unique = sorted(set(labels))
    index = {label: pos for pos, label in enumerate(unique)}
    counts = np.zeros((len(unique), len(unique)), dtype=int)
    for before, after in zip(labels[:-1], labels[1:]):
        counts[index[before], index[after]] += 1
    row_sums = counts.sum(axis=1, keepdims=True)
    probabilities = np.divide(counts, row_sums, out=np.zeros_like(counts, dtype=float), where=row_sums != 0)
    graph = [
        {
            "from_zone": unique[row],
            "to_zone": unique[col],
            "count": int(counts[row, col]),
            "probability": _json_float(probabilities[row, col]),
        }
        for row in range(len(unique))
        for col in range(len(unique))
        if counts[row, col] > 0
    ]
    return {
        "labels": unique,
        "probability_matrix": {
            "zones": unique,
            "counts": counts.tolist(),
            "probability": probabilities.tolist(),
        },
        "graph": graph,
    }


def _path_curvature(step_distance: np.ndarray, heading: np.ndarray) -> np.ndarray:
    if heading.size < 2:
        return np.zeros(0, dtype=float)
    yaw_delta = np.diff(heading)
    distances = step_distance[1:]
    result = np.zeros_like(yaw_delta, dtype=float)
    moving = distances > 1e-12
    result[moving] = yaw_delta[moving] / distances[moving]
    return result


def _dwell_time(labels: Sequence[str], timestep_s: float) -> dict[str, float | None]:
    return {
        label: _json_float(labels.count(label) * timestep_s)
        for label in sorted(set(labels))
    }


def _safe_probability(counts: np.ndarray) -> np.ndarray:
    total = float(np.sum(counts))
    return counts / total if total else np.zeros_like(counts, dtype=float)


def _entropy(counts: np.ndarray) -> float:
    probabilities = _safe_probability(np.asarray(counts, dtype=float)).ravel()
    probabilities = probabilities[probabilities > 0]
    return float(-np.sum(probabilities * np.log2(probabilities))) if probabilities.size else 0.0


def _revisit_count(heatmap: np.ndarray) -> int:
    return int(np.sum(np.maximum(heatmap - 1, 0)))


def _duration_s(sample_count: int, timestep_s: float) -> float:
    return max((sample_count - 1) * timestep_s, timestep_s)


def _size(arena: Arena) -> np.ndarray:
    size = np.asarray(arena.size_xy_mm, dtype=float)
    if size.shape != (2,) or not np.isfinite(size).all() or np.any(size <= 0):
        raise ValueError("rectangular arena requires positive size_xy_mm.")
    return size


def _positive_int(name: str, value: Any) -> int:
    result = int(value)
    if result <= 0:
        raise ValueError(f"{name} must be a positive integer.")
    return result


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


def _bounded_fraction(name: str, value: Any) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0 or result > 1:
        raise ValueError(f"{name} must be in the interval (0, 1].")
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


def _all_numbers_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_all_numbers_finite(item) for item in value.values())
    if isinstance(value, (list, tuple, np.ndarray)):
        return all(_all_numbers_finite(item) for item in value)
    if isinstance(value, (str, bool)) or value is None:
        return True
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return True


__all__ = ["analyze_open_field", "export_open_field_report"]
