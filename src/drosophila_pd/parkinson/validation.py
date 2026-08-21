"""Validation utilities for computational phenotype reports.

These functions quantify software-level repeatability and data sensitivity. They
do not assign biological meaning or clinical thresholds.
"""

from __future__ import annotations

import math
import re
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from .model import COMPUTATIONAL_SCOPE, ComputationalPDIndex


def bootstrap_confidence_interval(
    values: Sequence[float],
    *,
    statistic: Callable[[np.ndarray], float] = np.mean,
    replicates: int = 1000,
    seed: int = 0,
) -> dict[str, Any]:
    """Return a deterministic resampling interval for supplied observations."""

    array = np.asarray(values, dtype=float).ravel()
    if array.size == 0 or not np.isfinite(array).all():
        return {"available": False, "reason": "Finite observations are required.", "scope": COMPUTATIONAL_SCOPE}
    if int(replicates) <= 0:
        raise ValueError("replicates must be positive.")
    rng = np.random.default_rng(int(seed))
    estimates = np.asarray(
        [float(statistic(rng.choice(array, size=array.size, replace=True))) for _ in range(int(replicates))],
        dtype=float,
    )
    return {
        "available": True,
        "estimate": float(statistic(array)),
        "low": float(np.percentile(estimates, 2.5)),
        "high": float(np.percentile(estimates, 97.5)),
        "replicates": int(replicates),
        "seed": int(seed),
        "scope": "Computational resampling interval; not a significance or clinical interval.",
    }


def compare_feature_sets(
    observed: Mapping[str, float | None],
    reference: Mapping[str, float | None],
    *,
    feature_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Compute transparent deltas between two supplied feature mappings."""

    names = list(feature_names or sorted(set(observed) | set(reference)))
    rows: dict[str, Any] = {}
    for name in names:
        left = _finite_or_none(observed.get(name))
        right = _finite_or_none(reference.get(name))
        delta = left - right if left is not None and right is not None else None
        relative = delta / abs(right) if delta is not None and abs(right) > 1e-12 else None
        rows[name] = {"observed": left, "reference": right, "delta": delta, "relative_delta": relative, "available": delta is not None}
    return {"features": rows, "scope": COMPUTATIONAL_SCOPE}


def feature_ablation(
    index: ComputationalPDIndex,
    features: Mapping[str, float | None],
    reference: Mapping[str, float | None],
) -> dict[str, Any]:
    """Recompute an index with one configured component omitted at a time."""

    baseline = index._evaluate_core(features, reference)["value"]
    rows: dict[str, Any] = {}
    for name in index.weights:
        reduced = ComputationalPDIndex(
            weights={key: value for key, value in index.weights.items() if key != name},
            directions=index.directions,
        )
        value = reduced._evaluate_core(features, reference)["value"]
        rows[name] = {"index_without_feature": value, "delta_from_full": value - baseline if value is not None and baseline is not None else None}
    return {"full_index": baseline, "by_feature": rows, "scope": COMPUTATIONAL_SCOPE}


def leave_one_out_feature_validation(
    index: ComputationalPDIndex,
    feature_rows: Sequence[Mapping[str, float | None]],
    reference: Mapping[str, float | None],
) -> dict[str, Any]:
    """Report per-row index values without changing model configuration."""

    values = [index._evaluate_core(row, reference)["value"] for row in feature_rows]
    finite = [float(value) for value in values if value is not None and np.isfinite(value)]
    return {"sample_count": len(feature_rows), "finite_count": len(finite), "values": values, "scope": COMPUTATIONAL_SCOPE}


def cross_validate_index(
    index: ComputationalPDIndex,
    feature_rows: Sequence[Mapping[str, float | None]],
    reference: Mapping[str, float | None],
    *,
    folds: int = 5,
) -> dict[str, Any]:
    """Evaluate fixed configuration across deterministic contiguous folds."""

    if int(folds) <= 0:
        raise ValueError("folds must be positive")
    if not feature_rows:
        return {"available": False, "reason": "Feature rows are required.", "scope": COMPUTATIONAL_SCOPE}
    fold_count = min(int(folds), len(feature_rows))
    partitions = np.array_split(np.arange(len(feature_rows)), fold_count)
    results = []
    for fold, indices in enumerate(partitions):
        values = [index._evaluate_core(feature_rows[int(i)], reference)["value"] for i in indices]
        finite = [float(value) for value in values if value is not None and np.isfinite(value)]
        results.append({"fold": fold, "indices": indices.astype(int).tolist(), "values": values, "finite_count": len(finite)})
    return {"available": True, "folds": results, "scope": COMPUTATIONAL_SCOPE}


def correlation_matrix(samples: Mapping[str, Sequence[float]]) -> dict[str, Any]:
    """Compute pairwise Pearson correlations for finite supplied samples."""

    names = list(samples)
    matrix = np.full((len(names), len(names)), np.nan, dtype=float)
    for row, left_name in enumerate(names):
        for col, right_name in enumerate(names):
            left = np.asarray(samples[left_name], dtype=float).ravel()
            right = np.asarray(samples[right_name], dtype=float).ravel()
            size = min(left.size, right.size)
            if size and np.isfinite(left[:size]).all() and np.isfinite(right[:size]).all():
                if np.std(left[:size]) == 0 or np.std(right[:size]) == 0:
                    matrix[row, col] = 1.0 if row == col else 0.0
                else:
                    matrix[row, col] = float(np.corrcoef(left[:size], right[:size])[0, 1])
    return {"features": names, "values": matrix.tolist(), "scope": COMPUTATIONAL_SCOPE}


def outlier_sensitivity(values: Sequence[float]) -> dict[str, Any]:
    """Compare robust and non-robust summaries without removing observations."""

    array = np.asarray(values, dtype=float).ravel()
    finite = array[np.isfinite(array)]
    if finite.size == 0:
        return {"available": False, "scope": COMPUTATIONAL_SCOPE}
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - median)))
    return {
        "available": True,
        "mean": float(np.mean(finite)),
        "median": median,
        "std": float(np.std(finite)),
        "mad": mad,
        "iqr": float(np.percentile(finite, 75) - np.percentile(finite, 25)),
        "sample_count": int(finite.size),
        "scope": COMPUTATIONAL_SCOPE,
    }


def validate_computational_report(report: Mapping[str, Any]) -> dict[str, Any]:
    """Validate report structure, finite numeric payloads, and scope wording."""

    checks = {
        "has_scope": isinstance(report.get("scientific_scope"), str),
        "has_motor_features": isinstance(report.get("motor_features"), Mapping),
        "has_behavior_model": isinstance(report.get("behavior_model"), Mapping),
        "numeric_payload_finite": _all_finite(report),
        "scope_is_conservative": _scope_is_conservative(report.get("scientific_scope", "")),
    }
    return {"overall_pass": all(checks.values()), "checks": checks, "scope": COMPUTATIONAL_SCOPE}


def _scope_is_conservative(value: str) -> bool:
    required = ("computational", "not medical", "biological validation")
    text = value.lower()
    if not all(item in text for item in required):
        return False
    prohibited_upgrade = re.compile(r"\b(validated|confirms|establishes)\s+(biological|clinical|medical)")
    return prohibited_upgrade.search(text) is None


def _all_finite(value: Any) -> bool:
    if isinstance(value, Mapping):
        return all(_all_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_all_finite(item) for item in value)
    if isinstance(value, (float, int, np.floating, np.integer)) and not isinstance(value, bool):
        return math.isfinite(float(value))
    return True


def _finite_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


__all__ = [
    "bootstrap_confidence_interval",
    "compare_feature_sets",
    "correlation_matrix",
    "cross_validate_index",
    "feature_ablation",
    "leave_one_out_feature_validation",
    "outlier_sensitivity",
    "validate_computational_report",
]
