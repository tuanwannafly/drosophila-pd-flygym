"""Comparison helpers for computational phenotype reports."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from drosophila_pd.behavior_platform.behavior_comparison import compare_behavior_conditions

from .model import COMPUTATIONAL_SCOPE
from .validation import bootstrap_confidence_interval, compare_feature_sets


def compare_computational_reports(
    reports: Mapping[str, Mapping[str, Any]],
    *,
    reference_name: str | None = None,
    bootstrap_replicates: int = 0,
    bootstrap_seed: int = 0,
) -> dict[str, Any]:
    """Compare report features and existing behavioral report families."""

    if len(reports) < 2:
        raise ValueError("at least two reports are required")
    names = list(reports)
    reference_name = reference_name or names[0]
    if reference_name not in reports:
        raise ValueError(f"unknown reference report: {reference_name}")
    reference = reports[reference_name]["motor_features"]["values"]
    deltas = {
        name: compare_feature_sets(report["motor_features"]["values"], reference)
        for name, report in reports.items()
    }
    matrix = _feature_distance_matrix(reports)
    result: dict[str, Any] = {
        "comparison_version": 1,
        "conditions": names,
        "reference": reference_name,
        "feature_deltas": deltas,
        "feature_distance_matrix": {"conditions": names, "values": matrix.tolist()},
        "feature_rankings": _feature_rankings(reports),
        "effect_sizes": _effect_sizes(reports),
        "behavior_comparison": compare_behavior_conditions(
            {name: report["behavior_model"] if "trajectory" not in report else report for name, report in reports.items()}
        ) if all("trajectory" in report for report in reports.values()) else {"available": False, "reason": "Trajectory reports were not supplied in every condition."},
        "scope": COMPUTATIONAL_SCOPE,
    }
    if bootstrap_replicates > 0:
        result["reference_feature_intervals"] = _reference_intervals(
            reports, names, bootstrap_replicates, bootstrap_seed
        )
    return result


def _feature_distance_matrix(reports: Mapping[str, Mapping[str, Any]]) -> np.ndarray:
    names = list(reports)
    vectors = []
    for name in names:
        values = reports[name]["motor_features"]["values"]
        vectors.append(np.asarray([float(value) if value is not None else np.nan for value in values.values()], dtype=float))
    matrix = np.zeros((len(names), len(names)), dtype=float)
    for row, left in enumerate(vectors):
        for col, right in enumerate(vectors):
            mask = np.isfinite(left) & np.isfinite(right)
            matrix[row, col] = float(np.linalg.norm(left[mask] - right[mask])) if np.any(mask) else 0.0
    return matrix


def _reference_intervals(reports, names: Sequence[str], replicates: int, seed: int):
    intervals: dict[str, Any] = {}
    for offset, name in enumerate(names):
        samples = reports[name]["motor_features"].get("sample_values", {})
        intervals[name] = {
            feature: bootstrap_confidence_interval(series, replicates=replicates, seed=seed + offset)
            for feature, series in samples.items()
        }
    return intervals


def _feature_rankings(reports: Mapping[str, Mapping[str, Any]]) -> dict[str, list[str]]:
    feature_names = list(next(iter(reports.values()))["motor_features"]["values"])
    return {
        feature: [
            name for name, _ in sorted(
                ((name, reports[name]["motor_features"]["values"].get(feature)) for name in reports),
                key=lambda item: item[1] if item[1] is not None else -np.inf,
                reverse=True,
            )
        ]
        for feature in feature_names
    }


def _effect_sizes(reports: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    names = list(reports)
    output: dict[str, Any] = {}
    for left_index, left_name in enumerate(names):
        for right_name in names[left_index + 1 :]:
            pair = f"{left_name}__vs__{right_name}"
            rows = {}
            features = set(reports[left_name]["motor_features"]["values"]) | set(reports[right_name]["motor_features"]["values"])
            for feature in sorted(features):
                left = _samples_for_feature(reports[left_name], feature)
                right = _samples_for_feature(reports[right_name], feature)
                rows[feature] = _cohen_d(left, right)
            output[pair] = rows
    return output


def _samples_for_feature(report: Mapping[str, Any], feature: str) -> np.ndarray:
    samples = report["motor_features"].get("sample_values", {}).get(feature)
    if samples is None:
        value = report["motor_features"]["values"].get(feature)
        return np.asarray([] if value is None else [value], dtype=float)
    return np.asarray(samples, dtype=float).ravel()


def _cohen_d(left: np.ndarray, right: np.ndarray) -> float | None:
    if left.size < 2 or right.size < 2 or not np.isfinite(left).all() or not np.isfinite(right).all():
        return None
    pooled_variance = ((left.size - 1) * np.var(left, ddof=1) + (right.size - 1) * np.var(right, ddof=1)) / max(left.size + right.size - 2, 1)
    scale = float(np.sqrt(pooled_variance))
    return float((np.mean(left) - np.mean(right)) / scale) if scale > 1e-12 else 0.0


__all__ = ["compare_computational_reports"]
