"""Validation summaries for perturbation transformations."""

from __future__ import annotations

import math
from typing import Any

import numpy as np


def summarize_action_transformation(
    *,
    controller_joint_angle_actions: np.ndarray,
    applied_joint_angle_actions: np.ndarray,
    controller_adhesion_onoff: np.ndarray | None,
    applied_adhesion_onoff: np.ndarray | None,
    expected_joint_angle_count: int,
    perturbation_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    """Summarize whether applied actions match the declared perturbation."""

    controller_actions = np.asarray(controller_joint_angle_actions, dtype=float)
    applied_actions = np.asarray(applied_joint_angle_actions, dtype=float)
    action_dimensions_valid = (
        controller_actions.ndim == 2
        and applied_actions.ndim == 2
        and controller_actions.shape == applied_actions.shape
        and controller_actions.shape[1] == expected_joint_angle_count
    )
    adhesion_preserved = _adhesion_preserved(
        controller_adhesion_onoff, applied_adhesion_onoff
    )
    metadata_type = (
        perturbation_metadata.get("type") if perturbation_metadata is not None else None
    )
    expected_actions = controller_actions
    expected_transform = "identity"
    scale = _effective_component_scale(
        perturbation_metadata,
        component_type="global_action_scale",
    )
    if scale is not None:
        expected_actions = controller_actions * scale
        expected_transform = (
            "global_action_scale"
            if metadata_type == "global_action_scale"
            else "composite_global_action_scale"
        )

    transform_error = (
        _max_abs_difference(expected_actions, applied_actions)
        if action_dimensions_valid
        else None
    )
    transform_pass = (
        transform_error is not None
        and transform_error <= 1e-12
        and action_dimensions_valid
    )
    return {
        "perturbation_type": metadata_type,
        "expected_transform": expected_transform,
        "expected_scale": scale,
        "effective_joint_angle_scale": scale,
        "component_action_transforms": _component_transform_summaries(
            perturbation_metadata,
            stage="action",
        ),
        "controller_joint_angle_shape": [int(value) for value in controller_actions.shape],
        "applied_joint_angle_shape": [int(value) for value in applied_actions.shape],
        "expected_joint_angle_count": int(expected_joint_angle_count),
        "action_dimensions_valid": action_dimensions_valid,
        "adhesion_commands_preserved": adhesion_preserved,
        "joint_angle_transform_error_max": _json_float(transform_error),
        "joint_angle_transform_check": _check(True, transform_pass),
        "structural_checks": {
            "action_dimensions_valid": _check(True, action_dimensions_valid),
            "adhesion_commands_preserved": _check(True, adhesion_preserved),
            "joint_angle_transform_matches_expected": _check(True, transform_pass),
        },
    }


def summarize_controller_transformation(
    *,
    pre_controller_state: dict[str, Any],
    post_controller_state: dict[str, Any],
    perturbation_metadata: dict[str, Any] | None,
) -> dict[str, Any]:
    """Summarize whether controller state matches declared perturbations."""

    pre_weights = np.asarray(
        pre_controller_state.get("cpg_coupling_weights"),
        dtype=float,
    )
    post_weights = np.asarray(
        post_controller_state.get("cpg_coupling_weights"),
        dtype=float,
    )
    dimensions_valid = (
        pre_weights.ndim == 2
        and post_weights.ndim == 2
        and pre_weights.shape == post_weights.shape
    )
    metadata_type = (
        perturbation_metadata.get("type") if perturbation_metadata is not None else None
    )
    scale = _effective_component_scale(
        perturbation_metadata,
        component_type="cpg_coupling_scale",
    )
    expected_transform = "identity"
    expected_weights = pre_weights
    if scale is not None:
        expected_weights = pre_weights * scale
        expected_transform = (
            "cpg_coupling_scale"
            if metadata_type == "cpg_coupling_scale"
            else "composite_cpg_coupling_scale"
        )

    transform_error = (
        _max_abs_difference(expected_weights, post_weights)
        if dimensions_valid
        else None
    )
    transform_pass = (
        transform_error is not None
        and transform_error <= 1e-12
        and dimensions_valid
    )
    return {
        "perturbation_type": metadata_type,
        "expected_transform": expected_transform,
        "expected_cpg_coupling_scale": scale,
        "effective_cpg_coupling_scale": scale,
        "component_controller_transforms": _component_transform_summaries(
            perturbation_metadata,
            stage="controller",
        ),
        "cpg_coupling_shape_before": [int(value) for value in pre_weights.shape],
        "cpg_coupling_shape_after": [int(value) for value in post_weights.shape],
        "cpg_coupling_nonzero_before": _json_int_or_none(
            np.count_nonzero(pre_weights)
        ),
        "cpg_coupling_nonzero_after": _json_int_or_none(
            np.count_nonzero(post_weights)
        ),
        "cpg_coupling_abs_sum_before": _json_float(np.sum(np.abs(pre_weights))),
        "cpg_coupling_abs_sum_after": _json_float(np.sum(np.abs(post_weights))),
        "controller_dimensions_valid": dimensions_valid,
        "cpg_coupling_transform_error_max": _json_float(transform_error),
        "cpg_coupling_transform_check": _check(True, transform_pass),
        "structural_checks": {
            "controller_dimensions_valid": _check(True, dimensions_valid),
            "cpg_coupling_transform_matches_expected": _check(True, transform_pass),
        },
    }


def _adhesion_preserved(
    controller_adhesion_onoff: np.ndarray | None,
    applied_adhesion_onoff: np.ndarray | None,
) -> bool:
    if controller_adhesion_onoff is None and applied_adhesion_onoff is None:
        return True
    if controller_adhesion_onoff is None or applied_adhesion_onoff is None:
        return False
    controller = np.asarray(controller_adhesion_onoff, dtype=bool)
    applied = np.asarray(applied_adhesion_onoff, dtype=bool)
    return controller.shape == applied.shape and bool(np.array_equal(controller, applied))


def _max_abs_difference(left: np.ndarray, right: np.ndarray) -> float | None:
    if left.shape != right.shape or left.size == 0:
        return None
    difference = np.abs(left - right)
    if not np.isfinite(difference).all():
        return None
    return float(np.max(difference))


def _component_transform_summaries(
    perturbation_metadata: dict[str, Any] | None,
    *,
    stage: str,
) -> list[dict[str, Any]]:
    summaries = []
    for index, metadata in enumerate(_flatten_component_metadata(perturbation_metadata)):
        metadata_type = metadata.get("type")
        parameters = metadata.get("parameters", {})
        if stage == "action" and metadata_type == "global_action_scale":
            expected_transform = "joint_angle_scale"
            scale = parameters.get("scale")
        elif stage == "controller" and metadata_type == "cpg_coupling_scale":
            expected_transform = "cpg_coupling_scale"
            scale = parameters.get("scale")
        else:
            expected_transform = "identity"
            scale = None
        summaries.append(
            {
                "index": index,
                "type": metadata_type,
                "name": metadata.get("name"),
                "intervention_stage": metadata.get("intervention_stage"),
                "intervention_target": metadata.get("intervention_target"),
                "expected_transform": expected_transform,
                "scale": _json_float(scale),
            }
        )
    return summaries


def _effective_component_scale(
    perturbation_metadata: dict[str, Any] | None,
    *,
    component_type: str,
) -> float | None:
    scale = 1.0
    found = False
    for metadata in _flatten_component_metadata(perturbation_metadata):
        if metadata.get("type") != component_type:
            continue
        parameters = metadata.get("parameters", {})
        scale *= float(parameters["scale"])
        found = True
    return scale if found else None


def _flatten_component_metadata(
    perturbation_metadata: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if perturbation_metadata is None:
        return []
    if perturbation_metadata.get("type") != "composite":
        return [perturbation_metadata]
    flattened = []
    for component in perturbation_metadata.get("components", []):
        if isinstance(component, dict):
            flattened.extend(_flatten_component_metadata(component))
    return flattened


def _check(expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


def _json_float(value: Any) -> float | None:
    try:
        as_float = float(value)
    except (TypeError, ValueError):
        return None
    return as_float if math.isfinite(as_float) else None


def _json_int_or_none(value: Any) -> int | None:
    try:
        as_int = int(value)
    except (TypeError, ValueError):
        return None
    return as_int


__all__ = [
    "summarize_action_transformation",
    "summarize_controller_transformation",
]
