"""Behavioral assay suite composition."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from drosophila_pd.assays.base import RolloutAssayInput
from drosophila_pd.assays.freezing import FreezingAssay
from drosophila_pd.assays.gait import GaitAssay
from drosophila_pd.assays.open_field import OpenFieldAssay
from drosophila_pd.assays.turning import TurningAssay


DEFAULT_ASSAY_CONFIG: dict[str, Any] = {
    "open_field": {
        "enabled": True,
        "arena_center_xy_mm": [0.0, 0.0],
        "arena_size_mm": [100.0, 100.0],
        "center_fraction": 0.5,
        "border_width_mm": 10.0,
        "grid_bins": 8,
    },
    "freezing": {
        "enabled": True,
        "immobility_speed_threshold_mm_s": 1.0,
        "min_freezing_duration_s": 0.0,
    },
    "turning": {
        "enabled": True,
        "turn_rate_threshold_rad_s": 0.5,
        "min_turn_duration_s": 0.0,
        "turn_angle_histogram_bins": 16,
    },
    "gait": {
        "enabled": True,
    },
}


def run_behavioral_assay_suite(
    *,
    rollout: RolloutAssayInput,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate enabled behavioral assays over existing rollout outputs."""

    settings = _deep_merge(DEFAULT_ASSAY_CONFIG, config or {})
    results: dict[str, Any] = {
        "assay_suite_version": 1,
        "scientific_scope": (
            "Computational behavioral assays over existing rollout outputs only. "
            "The suite does not run simulations, introduce perturbations, modify "
            "controllers, validate Parkinson's disease, or make biological "
            "mechanistic claims."
        ),
        "configuration": settings,
        "assays": {},
    }

    if settings["open_field"].get("enabled", True):
        open_field_config = _without_enabled(settings["open_field"])
        results["assays"]["open_field"] = OpenFieldAssay(
            open_field_config
        ).evaluate(rollout).as_dict()

    if settings["freezing"].get("enabled", True):
        freezing_config = _without_enabled(settings["freezing"])
        results["assays"]["freezing"] = FreezingAssay(
            freezing_config
        ).evaluate(rollout).as_dict()

    if settings["turning"].get("enabled", True):
        turning_config = _without_enabled(settings["turning"])
        results["assays"]["turning"] = TurningAssay(
            turning_config
        ).evaluate(rollout).as_dict()

    if settings["gait"].get("enabled", True):
        results["assays"]["gait"] = GaitAssay().evaluate(rollout).as_dict()

    return results


def _without_enabled(config: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in config.items() if key != "enabled"}


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


__all__ = [
    "DEFAULT_ASSAY_CONFIG",
    "run_behavioral_assay_suite",
]
