"""Ground-truth comparison metrics for imported arrays and feature mappings."""

from __future__ import annotations

import math
from typing import Any, Mapping

import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData


def compare_series(observed: Any, reference: Any) -> dict[str, Any]:
    """Compare equal-length finite numeric arrays without resampling."""

    left = np.asarray(observed, dtype=float).ravel()
    right = np.asarray(reference, dtype=float).ravel()
    if left.shape != right.shape:
        return {"available": False, "reason": "shape mismatch", "observed_shape": list(left.shape), "reference_shape": list(right.shape)}
    if left.size == 0 or not np.isfinite(left).all() or not np.isfinite(right).all():
        return {"available": False, "reason": "finite non-empty arrays are required"}
    delta = left - right
    reference_scale = np.maximum(np.abs(right), 1e-12)
    centered = right - np.mean(right)
    residual = left - right
    ss_total = float(np.sum(centered**2))
    r2 = 1.0 - float(np.sum(residual**2)) / ss_total if ss_total > 1e-12 else (1.0 if np.allclose(left, right) else 0.0)
    correlation = _correlation(left, right)
    return {
        "available": True,
        "sample_count": int(left.size),
        "absolute_error_mean": float(np.mean(np.abs(delta))),
        "relative_error_mean": float(np.mean(np.abs(delta) / reference_scale)),
        "rmse": float(np.sqrt(np.mean(delta**2))),
        "mae": float(np.mean(np.abs(delta))),
        "r2": float(r2),
        "correlation": correlation,
        "observed_min": float(np.min(left)),
        "observed_max": float(np.max(left)),
        "reference_min": float(np.min(right)),
        "reference_max": float(np.max(right)),
    }


def compare_feature_mappings(
    observed: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare common numeric feature entries and report missing keys."""

    names = sorted(set(observed) | set(reference))
    results = {}
    for name in names:
        if name not in observed or name not in reference:
            results[name] = {"available": False, "reason": "feature missing from one mapping"}
        else:
            results[name] = compare_series(observed[name], reference[name])
    return {
        "features": results,
        "common_count": sum(item.get("available", False) for item in results.values()),
        "scope": "Numeric agreement against supplied reference observations only.",
    }


def compare_analysis_mappings(
    observed: Mapping[str, Any],
    reference: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare numeric leaves in supplied velocity/behavior/statistics reports."""

    left = _flatten_numeric(observed)
    right = _flatten_numeric(reference)
    return compare_feature_mappings(left, right)


def compare_rollouts(
    observed: RolloutData,
    reference: RolloutData,
    *,
    observed_features: Mapping[str, Any] | None = None,
    reference_features: Mapping[str, Any] | None = None,
    observed_analysis: Mapping[str, Any] | None = None,
    reference_analysis: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare trajectory, joints, COM and orientation from two rollouts."""

    fields: dict[str, Any] = {
        "trajectory": compare_series(observed.positions_array(), reference.positions_array()),
        "orientation": compare_series(observed.quaternions_array(), reference.quaternions_array()),
    }
    observed_com = observed.com_array()
    reference_com = reference.com_array()
    fields["com"] = compare_series(observed_com, reference_com) if observed_com is not None and reference_com is not None else {"available": False, "reason": "COM missing from one rollout"}
    joint_names = sorted(set(observed.joint_arrays()) | set(reference.joint_arrays()))
    fields["joints"] = {
        name: compare_series(observed.joint_arrays()[name], reference.joint_arrays()[name])
        if name in observed.joint_arrays() and name in reference.joint_arrays()
        else {"available": False, "reason": "joint missing from one rollout"}
        for name in joint_names
    }
    result = {
        "observed_condition_id": observed.condition_id,
        "reference_condition_id": reference.condition_id,
        "timestep_equal": bool(np.isclose(observed.timestep(), reference.timestep())),
        "fields": fields,
        "scope": "Raw rollout agreement only; this comparison is not biological validation.",
    }
    if observed_features is not None and reference_features is not None:
        result["features"] = compare_feature_mappings(observed_features, reference_features)
    if observed_analysis is not None and reference_analysis is not None:
        result["analysis"] = compare_analysis_mappings(observed_analysis, reference_analysis)
    return result


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    if np.std(left) <= 1e-12 or np.std(right) <= 1e-12:
        return 1.0 if np.allclose(left, right) else 0.0
    value = float(np.corrcoef(left, right)[0, 1])
    return value if math.isfinite(value) else 0.0


def _flatten_numeric(value: Any, prefix: str = "") -> dict[str, Any]:
    found: dict[str, Any] = {}
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            found.update(_flatten_numeric(item, child))
    elif isinstance(value, (list, tuple, np.ndarray)):
        array = np.asarray(value)
        if array.ndim == 0:
            found[prefix] = array.item()
        elif array.size and np.issubdtype(array.dtype, np.number):
            found[prefix] = array
    else:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return found
        if math.isfinite(number):
            found[prefix] = number
    return found


__all__ = ["compare_analysis_mappings", "compare_feature_mappings", "compare_rollouts", "compare_series"]
