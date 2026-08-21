"""Multi-condition behavioral similarity for Session08."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from drosophila_pd.behavior_platform.data_model import BehaviorComparison


def compare_behavior_conditions(
    conditions: Mapping[str, Mapping[str, Any]],
    *,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Compare Healthy, Candidate, progression, and intervention reports."""

    if len(conditions) < 2:
        raise ValueError("at least two behavior conditions are required.")
    names = list(conditions)
    metrics = {
        "trajectory_similarity": _pair_matrix(names, conditions, _trajectory_similarity),
        "dtw_distance": _pair_matrix(names, conditions, _dtw_distance),
        "frechet_distance": _pair_matrix(names, conditions, _frechet_distance),
        "occupancy_similarity": _pair_matrix(names, conditions, _occupancy_similarity),
        "gait_similarity": _pair_matrix(names, conditions, _gait_similarity),
        "turning_similarity": _pair_matrix(names, conditions, _turning_similarity),
        "exploration_similarity": _pair_matrix(names, conditions, _exploration_similarity),
    }
    aggregate = _aggregate_similarity(names, metrics)
    comparison = BehaviorComparison(
        comparison_id="multi_condition_behavior_comparison",
        conditions=names,
        similarity_matrix=aggregate,
        metadata={"metric_families": list(metrics)},
    )
    report = {
        "behavior_comparison_version": 2,
        "scientific_scope": (
            "Behavioral similarities compare simulated output arrays and "
            "reports only; roles are computational labels."
        ),
        "conditions": names,
        "metrics": metrics,
        "behavioral_similarity_matrix": aggregate,
        "comparison": comparison.as_dict(),
    }
    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report


def _pair_matrix(
    names: Sequence[str],
    conditions: Mapping[str, Mapping[str, Any]],
    metric,
) -> dict[str, Any]:
    values = np.zeros((len(names), len(names)), dtype=float)
    for row, left in enumerate(names):
        for col, right in enumerate(names):
            values[row, col] = metric(conditions[left], conditions[right])
    return {"conditions": list(names), "values": values.tolist()}


def _aggregate_similarity(names: Sequence[str], metrics: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    similarity_keys = [
        "trajectory_similarity",
        "occupancy_similarity",
        "gait_similarity",
        "turning_similarity",
        "exploration_similarity",
    ]
    matrices = [np.asarray(metrics[key]["values"], dtype=float) for key in similarity_keys]
    return {"conditions": list(names), "values": np.mean(matrices, axis=0).tolist()}


def _trajectory_similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    distance = _frechet_distance(left, right)
    return _bounded_similarity(distance)


def _dtw_distance(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    a = _trajectory_xy(left)
    b = _trajectory_xy(right)
    costs = np.full((a.shape[0] + 1, b.shape[0] + 1), np.inf)
    costs[0, 0] = 0.0
    for i in range(1, a.shape[0] + 1):
        for j in range(1, b.shape[0] + 1):
            step = np.linalg.norm(a[i - 1] - b[j - 1])
            costs[i, j] = step + min(costs[i - 1, j], costs[i, j - 1], costs[i - 1, j - 1])
    return _json_float(costs[-1, -1])


def _frechet_distance(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    a = _trajectory_xy(left)
    b = _trajectory_xy(right)
    cache = np.full((a.shape[0], b.shape[0]), -1.0)

    def rec(i: int, j: int) -> float:
        if cache[i, j] >= 0:
            return float(cache[i, j])
        distance = float(np.linalg.norm(a[i] - b[j]))
        if i == 0 and j == 0:
            value = distance
        elif i > 0 and j == 0:
            value = max(rec(i - 1, 0), distance)
        elif i == 0 and j > 0:
            value = max(rec(0, j - 1), distance)
        else:
            value = max(min(rec(i - 1, j), rec(i - 1, j - 1), rec(i, j - 1)), distance)
        cache[i, j] = value
        return value

    return _json_float(rec(a.shape[0] - 1, b.shape[0] - 1))


def _occupancy_similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    a = _heatmap(left)
    b = _heatmap(right)
    if a.shape != b.shape:
        size = min(a.shape[0], b.shape[0]), min(a.shape[1], b.shape[1])
        a = a[: size[0], : size[1]]
        b = b[: size[0], : size[1]]
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    return 1.0 if denom == 0 else _json_float(float(np.sum(a * b) / denom))


def _gait_similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    return _vector_similarity(_metric_vector(left, "gait"), _metric_vector(right, "gait"))


def _turning_similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    return _vector_similarity(_metric_vector(left, "turning"), _metric_vector(right, "turning"))


def _exploration_similarity(left: Mapping[str, Any], right: Mapping[str, Any]) -> float:
    return _vector_similarity(_metric_vector(left, "exploration"), _metric_vector(right, "exploration"))


def _trajectory_xy(report: Mapping[str, Any]) -> np.ndarray:
    if "trajectory" in report:
        trajectory = report["trajectory"]
        return np.column_stack([trajectory["x_mm"], trajectory["y_mm"]]).astype(float)
    if "positions_xy_mm" in report:
        return np.asarray(report["positions_xy_mm"], dtype=float)
    raise ValueError("condition report requires trajectory or positions_xy_mm.")


def _heatmap(report: Mapping[str, Any]) -> np.ndarray:
    if "heat_map" in report:
        return np.asarray(report["heat_map"]["counts"], dtype=float)
    if "open_field" in report and "heat_map" in report["open_field"]:
        return np.asarray(report["open_field"]["heat_map"]["counts"], dtype=float)
    return np.zeros((1, 1), dtype=float)


def _metric_vector(report: Mapping[str, Any], family: str) -> np.ndarray:
    if family == "gait" and "gait_analysis" in report:
        return _numbers(report["gait_analysis"].get("gait_stability", {}))
    if family == "turning":
        return _numbers(report.get("turning_summary", report.get("turning", {})))
    if family == "exploration":
        values = {
            "center": report.get("center_occupancy"),
            "border": report.get("border_occupancy"),
            "entropy": report.get("exploration_entropy_bits"),
            "coverage": report.get("coverage_ratio"),
        }
        return _numbers(values)
    return np.zeros(1, dtype=float)


def _numbers(value: Any) -> np.ndarray:
    found: list[float] = []
    if isinstance(value, Mapping):
        for item in value.values():
            found.extend(_numbers(item).tolist())
    elif isinstance(value, (list, tuple)):
        for item in value:
            found.extend(_numbers(item).tolist())
    else:
        try:
            number = float(value)
            if math.isfinite(number):
                found.append(number)
        except (TypeError, ValueError):
            pass
    return np.asarray(found or [0.0], dtype=float)


def _vector_similarity(left: np.ndarray, right: np.ndarray) -> float:
    size = min(left.size, right.size)
    if size == 0:
        return 1.0
    distance = float(np.linalg.norm(left[:size] - right[:size]))
    return _bounded_similarity(distance)


def _bounded_similarity(distance: float) -> float:
    return _json_float(1.0 / (1.0 + max(0.0, float(distance))))


def _json_float(value: Any) -> float:
    result = float(value)
    return result if math.isfinite(result) else 0.0


__all__ = ["compare_behavior_conditions"]
