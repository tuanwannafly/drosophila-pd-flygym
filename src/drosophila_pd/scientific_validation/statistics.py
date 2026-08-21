"""Statistical stability checks over supplied observation arrays."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from drosophila_pd.parkinson.validation import bootstrap_confidence_interval, outlier_sensitivity


def validate_statistical_stability(
    samples: Mapping[str, Sequence[float]],
    *,
    replicates: int = 1000,
    seed: int = 0,
    folds: int = 5,
) -> dict[str, Any]:
    """Summarize bootstrap, fold, sensitivity and outlier stability."""

    results: dict[str, Any] = {}
    for name, values in samples.items():
        array = np.asarray(values, dtype=float).ravel()
        finite = array[np.isfinite(array)]
        results[name] = {
            "bootstrap": bootstrap_confidence_interval(finite, replicates=replicates, seed=seed),
            "cross_validation": _fold_stability(finite, folds),
            "feature_sensitivity": _feature_sensitivity(finite),
            "outlier_sensitivity": outlier_sensitivity(finite),
        }
    return {"features": results, "scope": "Computational stability summaries; no significance or biological inference."}


def effect_size_consistency(left: Sequence[float], right: Sequence[float]) -> dict[str, Any]:
    """Return Cohen's d and direction for two supplied sample arrays."""

    a = np.asarray(left, dtype=float).ravel()
    b = np.asarray(right, dtype=float).ravel()
    if a.size < 2 or b.size < 2 or not np.isfinite(a).all() or not np.isfinite(b).all():
        return {"available": False, "reason": "At least two finite observations per group are required."}
    pooled = ((a.size - 1) * np.var(a, ddof=1) + (b.size - 1) * np.var(b, ddof=1)) / (a.size + b.size - 2)
    scale = float(np.sqrt(pooled))
    value = float((np.mean(a) - np.mean(b)) / scale) if scale > 1e-12 else 0.0
    return {"available": True, "cohens_d": value, "direction": "left_greater" if value > 0 else "right_greater" if value < 0 else "equal", "scope": "Descriptive computational effect size; not a biological or significance claim."}


def _fold_stability(values: np.ndarray, folds: int) -> dict[str, Any]:
    if values.size == 0:
        return {"available": False, "reason": "Finite observations are required."}
    fold_count = min(max(int(folds), 1), values.size)
    means = [float(np.mean(part)) for part in np.array_split(values, fold_count)]
    return {"available": True, "fold_count": fold_count, "fold_means": means, "mean_of_fold_means": float(np.mean(means)), "std_of_fold_means": float(np.std(means))}


def _feature_sensitivity(values: np.ndarray) -> dict[str, Any]:
    if values.size == 0:
        return {"available": False, "reason": "Finite observations are required."}
    mean = float(np.mean(values))
    return {"available": True, "sample_count": int(values.size), "range": float(np.ptp(values)), "relative_range": float(np.ptp(values) / max(abs(mean), 1e-12))}


__all__ = ["effect_size_consistency", "validate_statistical_stability"]
