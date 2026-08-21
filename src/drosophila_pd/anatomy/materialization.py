"""Milestone 8B joint materialization and post-materialization validation."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .audit import (
    AuditError,
    AuditSafetyError,
    collect_block_8_12_observations,
    git_commit,
    instantiate_neuromechfly,
    runtime_environment,
    write_json_report,
)
from .orientation import add_joints_orientation


MATERIALIZATION_GATE_NAME = "materialize_joints_explicit_gate"

HISTORICAL_BLOCKS_8B = (
    {
        "block": "8.14",
        "classification": "READ_ONLY",
        "purpose": (
            "Create a local base skeleton via _get_base_skeleton(), inspect "
            "skeleton/MJCF body coverage, and confirm joint mappings remain empty."
        ),
    },
    {
        "block": "8.15",
        "classification": "READ_ONLY",
        "purpose": (
            "Use Skeleton.iter_jointdofs() to verify 204 unique JointDOFs, "
            "axis counts, leg counts, body coverage, and empty mappings."
        ),
    },
    {
        "block": "8.16",
        "classification": "DIAGNOSTIC_ONLY",
        "purpose": (
            "Inspect and disassemble BaseFly.add_joints() to locate the "
            "materialization boundary without calling it."
        ),
    },
    {
        "block": "8.17",
        "classification": "DIAGNOSTIC_ONLY",
        "purpose": (
            "Inspect BaseFly.add_actuators(), actuator enums, actuator mappings, "
            "and MJCF actuator state without creating actuators."
        ),
    },
    {
        "block": "8.18",
        "classification": "READ_ONLY",
        "purpose": (
            "Compare pre-materialization MJCF joint inventory with skeleton "
            "JointDOFs and confirm no MJCF joints or joint mappings exist yet."
        ),
    },
    {
        "block": "8.19A",
        "classification": "DIAGNOSTIC_ONLY",
        "purpose": (
            "Discover Skeleton traversal APIs and verify the pre-materialization "
            "MJCF/body mapping state."
        ),
    },
    {
        "block": "8.19B",
        "classification": "READ_ONLY",
        "purpose": (
            "Verify body segments, anatomical joints, JointDOFs, parent/child "
            "coverage, and the pre-materialization MJCF joint state."
        ),
    },
)

MILESTONE_8B_DEPENDENCY_GRAPH = {
    "pre_materialization_state": [
        "Block 8.12 frozen invariants",
        "Blocks 8.14, 8.15, 8.18, 8.19B read-only structural audits",
    ],
    "materialization_source_boundary": [
        "Block 8.16 add_joints source trace",
        "FlyGym 2.1.0 BaseFly.add_joints implementation",
    ],
    "actuator_non_goal": [
        "Block 8.17 actuator path trace",
        "FlyGym 2.1.0 BaseFly.add_actuators implementation",
    ],
    "post_materialization_state": [
        "Explicit gate calls fly.add_joints(base_skeleton) exactly once",
        "Validate skeleton, MJCF joint, neutral-angle, and actuator mappings",
    ],
}

EXPECTED_MILESTONE_8B: dict[str, Any] = {
    "python_major_minor": "3.12",
    "flygym_version": "2.1.0",
    "mujoco_version": "3.9.0",
    "fly_type": "flygym.compose.fly.neuromechfly.NeuroMechFly",
    "pre_skeleton_is_none": True,
    "pre_jointdof_to_mjcfjoint_length": 0,
    "pre_jointdof_to_neutralangle_length": 0,
    "pre_actuator_mapping_total_length": 0,
    "pre_neutralaction_mapping_total_length": 0,
    "pre_mjcf_root_joint_count": 0,
    "pre_mjcf_root_actuator_count": 0,
    "source_add_joints_changes_self_skeleton": True,
    "source_add_joints_creates_mjcf_joints": True,
    "source_add_joints_populates_joint_mappings": True,
    "source_add_joints_populates_neutral_angle_mapping": True,
    "source_add_joints_rebuilds_neutral_keyframes": True,
    "materialization_gate_used": True,
    "materialized_joint_count": 204,
    "post_skeleton_is_none": False,
    "post_skeleton_is_materialized_skeleton": True,
    "post_skeleton_type": "flygym.anatomy.Skeleton",
    "post_body_segment_count": 69,
    "post_anatomical_joint_count": 68,
    "post_jointdof_count": 204,
    "post_axis_counts": {"pitch": 68, "roll": 68, "yaw": 68},
    "post_jointdof_unique_name_count": 204,
    "post_bodyseg_to_mjcfbody_length": 69,
    "post_missing_parent_mjcf_body_count": 0,
    "post_missing_child_mjcf_body_count": 0,
    "post_jointdof_to_mjcfjoint_length": 204,
    "post_jointdof_to_neutralangle_length": 204,
    "post_mjcf_root_joint_count": 204,
    "post_joint_mapping_names_match_skeleton": True,
    "post_neutralangle_names_match_skeleton": True,
    "post_created_joint_names_match_skeleton": True,
    "post_mjcf_joint_names_match_skeleton": True,
    "post_all_neutral_angles_zero": True,
    "post_actuator_mapping_total_length": 0,
    "post_neutralaction_mapping_total_length": 0,
    "post_mjcf_root_actuator_count": 0,
    "transition_skeleton_none_to_materialized": True,
    "transition_joint_mapping_delta": 204,
    "transition_neutralangle_mapping_delta": 204,
    "transition_mjcf_root_joint_delta": 204,
    "transition_actuator_mapping_delta": 0,
    "transition_neutralaction_mapping_delta": 0,
    "transition_mjcf_root_actuator_delta": 0,
    "gate_rejects_second_materialization": True,
}


class MaterializationError(AuditError):
    """Raised when Milestone 8B cannot be completed."""


class MaterializationSafetyError(AuditSafetyError):
    """Raised when the explicit materialization gate is not safe to enter."""


def collect_pre_materialization_snapshot(fly: Any) -> dict[str, Any]:
    """Collect the frozen pre-materialization state before entering the gate."""

    observations = collect_block_8_12_observations(fly)
    return {
        **observations,
        "mjcf_root_joint_count": _mjcf_root_collection_length(fly, "joints"),
        "mjcf_root_actuator_count": _mjcf_root_collection_length(fly, "actuators"),
        "actuator_mapping_total_length": _nested_mapping_total_length(
            getattr(fly, "jointdof_to_mjcfactuator_by_type", {})
        ),
        "neutralaction_mapping_total_length": _nested_mapping_total_length(
            getattr(fly, "jointdof_to_neutralaction_by_type", {})
        ),
    }


def assert_materialization_pre_state(fly: Any) -> None:
    """Assert that the live fly is still safe for the one authorized gate call."""

    if not hasattr(fly, "skeleton"):
        raise MaterializationSafetyError("Fly object has no skeleton attribute.")
    if fly.skeleton is not None:
        raise MaterializationSafetyError("Expected fly.skeleton is None before gate.")

    _assert_attr_length(fly, "jointdof_to_mjcfjoint", 0)
    _assert_attr_length(fly, "jointdof_to_neutralangle", 0)
    _assert_nested_mapping_empty(fly, "jointdof_to_mjcfactuator_by_type")
    _assert_nested_mapping_empty(fly, "jointdof_to_neutralaction_by_type")
    _assert_mjcf_root_collection_length(fly, "joints", 0)
    _assert_mjcf_root_collection_length(fly, "actuators", 0)


def build_base_skeleton_for_materialization(fly: Any) -> Any:
    """Build the local base skeleton used by the explicit materialization gate."""

    if not hasattr(fly, "_get_base_skeleton"):
        raise MaterializationError("Fly object does not expose _get_base_skeleton().")

    skeleton = fly._get_base_skeleton()
    if fly.skeleton is not None:
        raise MaterializationSafetyError(
            "_get_base_skeleton() unexpectedly changed fly.skeleton."
        )
    return skeleton


def materialize_joints_explicit_gate(fly: Any, skeleton: Any) -> dict[Any, Any]:
    """The only repository function allowed to call `fly.add_joints(...)`."""

    assert_materialization_pre_state(fly)
    if skeleton is None:
        raise MaterializationSafetyError("A local skeleton is required.")
    return fly.add_joints(skeleton)


def collect_post_materialization_snapshot(
    fly: Any, *, materialized_skeleton: Any, created_joints: dict[Any, Any]
) -> dict[str, Any]:
    """Collect post-gate invariants without creating actuators or simulations."""

    skeleton = getattr(fly, "skeleton", None)
    if skeleton is None:
        raise MaterializationSafetyError("Expected fly.skeleton to be materialized.")

    jointdofs = list(skeleton.iter_jointdofs(root=fly.root_segment))
    jointdof_names = [_object_name(jointdof) for jointdof in jointdofs]
    jointdof_name_set = set(jointdof_names)
    body_segments = list(getattr(skeleton, "body_segments"))
    anatomical_joints = list(getattr(skeleton, "anatomical_joints"))

    body_mapping = dict(getattr(fly, "bodyseg_to_mjcfbody", {}))
    mapped_body_segment_names = {_object_name(key) for key in body_mapping}
    missing_parent_names = sorted(
        {
            _object_name(jointdof.parent)
            for jointdof in jointdofs
            if _object_name(jointdof.parent) not in mapped_body_segment_names
        }
    )
    missing_child_names = sorted(
        {
            _object_name(jointdof.child)
            for jointdof in jointdofs
            if _object_name(jointdof.child) not in mapped_body_segment_names
        }
    )

    joint_mapping = dict(getattr(fly, "jointdof_to_mjcfjoint", {}))
    neutral_mapping = dict(getattr(fly, "jointdof_to_neutralangle", {}))
    joint_mapping_names = {_object_name(key) for key in joint_mapping}
    neutral_mapping_names = {_object_name(key) for key in neutral_mapping}
    created_joint_names = {_object_name(key) for key in created_joints}
    mjcf_joint_names = {
        _object_name(value)
        for value in joint_mapping.values()
        if _object_name(value) is not None
    }

    return {
        "skeleton_is_none": skeleton is None,
        "skeleton_type": _qualified_type_name(skeleton),
        "skeleton_is_materialized_skeleton": skeleton is materialized_skeleton,
        "body_segment_count": len(body_segments),
        "anatomical_joint_count": len(anatomical_joints),
        "jointdof_count": len(jointdofs),
        "axis_counts": _axis_counts(jointdofs),
        "jointdof_unique_name_count": len(jointdof_name_set),
        "jointdof_first_names": jointdof_names[:15],
        "bodyseg_to_mjcfbody_length": len(body_mapping),
        "missing_parent_mjcf_body_count": len(missing_parent_names),
        "missing_parent_mjcf_body_names": missing_parent_names,
        "missing_child_mjcf_body_count": len(missing_child_names),
        "missing_child_mjcf_body_names": missing_child_names,
        "jointdof_to_mjcfjoint_length": len(joint_mapping),
        "jointdof_to_neutralangle_length": len(neutral_mapping),
        "mjcf_root_joint_count": _mjcf_root_collection_length(fly, "joints"),
        "joint_mapping_names_match_skeleton": joint_mapping_names == jointdof_name_set,
        "neutralangle_names_match_skeleton": neutral_mapping_names == jointdof_name_set,
        "created_joint_names_match_skeleton": created_joint_names == jointdof_name_set,
        "mjcf_joint_names_match_skeleton": mjcf_joint_names == jointdof_name_set,
        "all_neutral_angles_zero": all(
            _is_zero(value) for value in neutral_mapping.values()
        ),
        "jointdof_to_mjcfactuator_by_type_lengths": _mapping_lengths_by_type(
            getattr(fly, "jointdof_to_mjcfactuator_by_type", {})
        ),
        "jointdof_to_neutralaction_by_type_lengths": _mapping_lengths_by_type(
            getattr(fly, "jointdof_to_neutralaction_by_type", {})
        ),
        "actuator_mapping_total_length": _nested_mapping_total_length(
            getattr(fly, "jointdof_to_mjcfactuator_by_type", {})
        ),
        "neutralaction_mapping_total_length": _nested_mapping_total_length(
            getattr(fly, "jointdof_to_neutralaction_by_type", {})
        ),
        "mjcf_root_actuator_count": _mjcf_root_collection_length(fly, "actuators"),
    }


def build_milestone_8b_materialization_report(
    fly: Any, *, repo_root: str | Path | None = None
) -> dict[str, Any]:
    """Run Milestone 8B and return a JSON-serializable validation report."""

    pre = collect_pre_materialization_snapshot(fly)
    assert_materialization_pre_state(fly)
    source = add_joints_orientation(fly)
    skeleton = build_base_skeleton_for_materialization(fly)
    created_joints = materialize_joints_explicit_gate(fly, skeleton)
    materialization = {
        "gate_function": MATERIALIZATION_GATE_NAME,
        "operation": "fly.add_joints(base_skeleton)",
        "created_joint_count": len(created_joints),
        "created_joint_first_names": [
            _object_name(jointdof) for jointdof in list(created_joints)[:15]
        ],
    }
    post = collect_post_materialization_snapshot(
        fly,
        materialized_skeleton=skeleton,
        created_joints=created_joints,
    )
    transition = state_transition(pre, materialization, post)
    historical_comparison = compare_to_historical_blocks(pre, source, post)
    observed = {
        **runtime_environment(),
        "fly_type": pre["fly_type"],
        "pre": pre,
        "source": source,
        "materialization": materialization,
        "post": post,
        "transition": transition,
        "historical_comparison": historical_comparison,
    }
    checks = compare_milestone_8b(observed)
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "historical_blocks": list(HISTORICAL_BLOCKS_8B),
        "dependency_graph": MILESTONE_8B_DEPENDENCY_GRAPH,
        "expected_milestone": EXPECTED_MILESTONE_8B,
        "observed": observed,
        "checks": checks,
        "overall_pass": all(item["pass"] for item in checks.values()),
        "scientific_scope": (
            "Milestone 8B validates FlyGym/NeuroMechFly joint materialization "
            "and post-materialization anatomy mappings only. It does not create "
            "actuators, run locomotion, implement controllers, or validate a "
            "Parkinson's disease model."
        ),
    }


def build_milestone_8b_unavailable_report(
    error: BaseException, *, repo_root: str | Path | None = None
) -> dict[str, Any]:
    """Build a report for environments that cannot execute Milestone 8B."""

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "historical_blocks": list(HISTORICAL_BLOCKS_8B),
        "dependency_graph": MILESTONE_8B_DEPENDENCY_GRAPH,
        "expected_milestone": EXPECTED_MILESTONE_8B,
        "observed": runtime_environment(),
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
    }


def state_transition(
    pre: dict[str, Any], materialization: dict[str, Any], post: dict[str, Any]
) -> dict[str, Any]:
    """Summarize the exact pre-gate to post-gate changes."""

    return {
        "skeleton_none_to_materialized": (
            pre["skeleton_after_is_none"] and not post["skeleton_is_none"]
        ),
        "joint_mapping_delta": (
            post["jointdof_to_mjcfjoint_length"]
            - pre["jointdof_to_mjcfjoint_length"]
        ),
        "neutralangle_mapping_delta": (
            post["jointdof_to_neutralangle_length"]
            - pre["jointdof_to_neutralangle_length"]
        ),
        "mjcf_root_joint_delta": (
            post["mjcf_root_joint_count"] - pre["mjcf_root_joint_count"]
        ),
        "actuator_mapping_delta": (
            post["actuator_mapping_total_length"]
            - pre["actuator_mapping_total_length"]
        ),
        "neutralaction_mapping_delta": (
            post["neutralaction_mapping_total_length"]
            - pre["neutralaction_mapping_total_length"]
        ),
        "mjcf_root_actuator_delta": (
            post["mjcf_root_actuator_count"] - pre["mjcf_root_actuator_count"]
        ),
        "materialization_gate_used": (
            materialization["gate_function"] == MATERIALIZATION_GATE_NAME
        ),
    }


def compare_to_historical_blocks(
    pre: dict[str, Any], source: dict[str, Any], post: dict[str, Any]
) -> list[dict[str, Any]]:
    """Record the canonical equivalent of the scientifically relevant notebook facts."""

    return [
        _historical_row(
            "8.14/8.15/8.19B",
            "Local base skeleton exposes 69 body segments, 68 anatomical joints, "
            "and 204 JointDOFs.",
            {
                "pre_body_segments": pre["body_segment_count"],
                "pre_anatomical_joints": pre["anatomical_joint_count"],
                "pre_jointdofs": pre["jointdof_count"],
                "post_jointdofs": post["jointdof_count"],
            },
            "Skeleton.iter_jointdofs() and Skeleton anatomical/body collections.",
            True,
        ),
        _historical_row(
            "8.14/8.15/8.18/8.19",
            "Before materialization, fly.skeleton is None and joint mappings are empty.",
            {
                "pre_skeleton_is_none": pre["skeleton_after_is_none"],
                "pre_joint_mapping": pre["jointdof_to_mjcfjoint_length"],
                "pre_neutral_mapping": pre["jointdof_to_neutralangle_length"],
            },
            "BaseFly initializes skeleton to None and joint mappings to empty dicts.",
            True,
        ),
        _historical_row(
            "8.16",
            "BaseFly.add_joints() is the materialization boundary.",
            {
                "changes_self_skeleton": source["source_facts"][
                    "changes_self_skeleton"
                ],
                "creates_mjcf_joints": source["source_facts"][
                    "creates_mjcf_joints"
                ],
                "populates_joint_mappings": source["source_facts"][
                    "populates_joint_mappings"
                ],
            },
            "Source inspection of BaseFly.add_joints().",
            True,
        ),
        _historical_row(
            "8.17",
            "Actuator path is inspected but actuators are not created.",
            {
                "post_actuator_mapping_total": post["actuator_mapping_total_length"],
                "post_mjcf_root_actuators": post["mjcf_root_actuator_count"],
            },
            "Milestone 8B never calls BaseFly.add_actuators().",
            True,
        ),
        _historical_row(
            "8.18/8.19",
            "Pre-materialization MJCF joints are absent; after the authorized gate, "
            "every skeleton JointDOF has a matching MJCF joint.",
            {
                "pre_mjcf_root_joints": pre["mjcf_root_joint_count"],
                "post_mjcf_root_joints": post["mjcf_root_joint_count"],
                "post_mapping_names_match": post["joint_mapping_names_match_skeleton"],
            },
            "BaseFly.add_joints() adds hinge joints and updates joint mappings.",
            True,
            discrepancy=(
                "Historical cells stopped before the mutating call; this milestone "
                "executes it once by explicit authorization."
            ),
        ),
    ]


def compare_milestone_8b(
    observed: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Compare observed Milestone 8B values to expected state-transition facts."""

    pre = observed["pre"]
    source = observed["source"]
    materialization = observed["materialization"]
    post = observed["post"]
    transition = observed["transition"]
    observed_values = {
        "python_major_minor": observed.get("python_major_minor"),
        "flygym_version": observed.get("flygym_version"),
        "mujoco_version": observed.get("mujoco_version"),
        "fly_type": observed.get("fly_type"),
        "pre_skeleton_is_none": pre["skeleton_after_is_none"],
        "pre_jointdof_to_mjcfjoint_length": pre["jointdof_to_mjcfjoint_length"],
        "pre_jointdof_to_neutralangle_length": pre[
            "jointdof_to_neutralangle_length"
        ],
        "pre_actuator_mapping_total_length": pre["actuator_mapping_total_length"],
        "pre_neutralaction_mapping_total_length": pre[
            "neutralaction_mapping_total_length"
        ],
        "pre_mjcf_root_joint_count": pre["mjcf_root_joint_count"],
        "pre_mjcf_root_actuator_count": pre["mjcf_root_actuator_count"],
        "source_add_joints_changes_self_skeleton": source["source_facts"][
            "changes_self_skeleton"
        ],
        "source_add_joints_creates_mjcf_joints": source["source_facts"][
            "creates_mjcf_joints"
        ],
        "source_add_joints_populates_joint_mappings": source["source_facts"][
            "populates_joint_mappings"
        ],
        "source_add_joints_populates_neutral_angle_mapping": source["source_facts"][
            "populates_neutral_angle_mapping"
        ],
        "source_add_joints_rebuilds_neutral_keyframes": source["source_facts"][
            "rebuilds_neutral_keyframes"
        ],
        "materialization_gate_used": transition["materialization_gate_used"],
        "materialized_joint_count": materialization["created_joint_count"],
        "post_skeleton_is_none": post["skeleton_is_none"],
        "post_skeleton_is_materialized_skeleton": post[
            "skeleton_is_materialized_skeleton"
        ],
        "post_skeleton_type": post["skeleton_type"],
        "post_body_segment_count": post["body_segment_count"],
        "post_anatomical_joint_count": post["anatomical_joint_count"],
        "post_jointdof_count": post["jointdof_count"],
        "post_axis_counts": post["axis_counts"],
        "post_jointdof_unique_name_count": post["jointdof_unique_name_count"],
        "post_bodyseg_to_mjcfbody_length": post["bodyseg_to_mjcfbody_length"],
        "post_missing_parent_mjcf_body_count": post[
            "missing_parent_mjcf_body_count"
        ],
        "post_missing_child_mjcf_body_count": post["missing_child_mjcf_body_count"],
        "post_jointdof_to_mjcfjoint_length": post["jointdof_to_mjcfjoint_length"],
        "post_jointdof_to_neutralangle_length": post[
            "jointdof_to_neutralangle_length"
        ],
        "post_mjcf_root_joint_count": post["mjcf_root_joint_count"],
        "post_joint_mapping_names_match_skeleton": post[
            "joint_mapping_names_match_skeleton"
        ],
        "post_neutralangle_names_match_skeleton": post[
            "neutralangle_names_match_skeleton"
        ],
        "post_created_joint_names_match_skeleton": post[
            "created_joint_names_match_skeleton"
        ],
        "post_mjcf_joint_names_match_skeleton": post[
            "mjcf_joint_names_match_skeleton"
        ],
        "post_all_neutral_angles_zero": post["all_neutral_angles_zero"],
        "post_actuator_mapping_total_length": post["actuator_mapping_total_length"],
        "post_neutralaction_mapping_total_length": post[
            "neutralaction_mapping_total_length"
        ],
        "post_mjcf_root_actuator_count": post["mjcf_root_actuator_count"],
        "transition_skeleton_none_to_materialized": transition[
            "skeleton_none_to_materialized"
        ],
        "transition_joint_mapping_delta": transition["joint_mapping_delta"],
        "transition_neutralangle_mapping_delta": transition[
            "neutralangle_mapping_delta"
        ],
        "transition_mjcf_root_joint_delta": transition["mjcf_root_joint_delta"],
        "transition_actuator_mapping_delta": transition["actuator_mapping_delta"],
        "transition_neutralaction_mapping_delta": transition[
            "neutralaction_mapping_delta"
        ],
        "transition_mjcf_root_actuator_delta": transition[
            "mjcf_root_actuator_delta"
        ],
        "gate_rejects_second_materialization": _gate_rejects_current_state(post),
    }
    return {
        name: {
            "expected": expected,
            "observed": observed_values.get(name),
            "pass": observed_values.get(name) == expected,
        }
        for name, expected in EXPECTED_MILESTONE_8B.items()
    }


def _assert_attr_length(fly: Any, attr_name: str, expected: int) -> None:
    if not hasattr(fly, attr_name):
        raise MaterializationSafetyError(f"Fly object has no {attr_name} attribute.")
    observed = len(getattr(fly, attr_name))
    if observed != expected:
        raise MaterializationSafetyError(
            f"Expected {attr_name} length {expected} before gate; observed {observed}."
        )


def _assert_mjcf_root_collection_length(
    fly: Any, collection_name: str, expected: int
) -> None:
    observed = _mjcf_root_collection_length(fly, collection_name)
    if observed != expected:
        raise MaterializationSafetyError(
            f"Expected mjcf_root.{collection_name} length {expected} before gate; "
            f"observed {observed}."
        )


def _assert_nested_mapping_empty(fly: Any, attr_name: str) -> None:
    if not hasattr(fly, attr_name):
        raise MaterializationSafetyError(f"Fly object has no {attr_name} attribute.")
    total = _nested_mapping_total_length(getattr(fly, attr_name))
    if total != 0:
        raise MaterializationSafetyError(
            f"Expected nested {attr_name} mappings to be empty before gate; "
            f"observed total length {total}."
        )


def _axis_counts(jointdofs: list[Any]) -> dict[str, int]:
    counts = Counter(_enum_value(getattr(jointdof, "axis")) for jointdof in jointdofs)
    return {axis: counts.get(axis, 0) for axis in ("pitch", "roll", "yaw")}


def _enum_name(value: Any) -> str:
    return str(getattr(value, "name", value))


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _gate_rejects_current_state(post: dict[str, Any]) -> bool:
    return (
        post["skeleton_is_none"] is False
        and post["jointdof_to_mjcfjoint_length"] > 0
        and post["jointdof_to_neutralangle_length"] > 0
    )


def _historical_row(
    blocks: str,
    historical_invariant: str,
    canonical_invariant: dict[str, Any],
    source_api_justification: str,
    equivalent: bool,
    *,
    discrepancy: str | None = None,
) -> dict[str, Any]:
    return {
        "blocks": blocks,
        "historical_invariant": historical_invariant,
        "canonical_invariant": canonical_invariant,
        "source_api_justification": source_api_justification,
        "equivalent": equivalent,
        "discrepancy": discrepancy,
    }


def _is_zero(value: Any) -> bool:
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return value == 0


def _mapping_lengths_by_type(mapping_by_type: Any) -> dict[str, int]:
    return {
        _enum_name(mapping_type): len(mapping)
        for mapping_type, mapping in dict(mapping_by_type).items()
    }


def _mjcf_root_collection_length(fly: Any, collection_name: str) -> int | None:
    root = getattr(fly, "mjcf_root", None)
    if root is None or not hasattr(root, collection_name):
        return None
    try:
        return len(getattr(root, collection_name))
    except TypeError:
        return None


def _nested_mapping_total_length(mapping_by_type: Any) -> int:
    return sum(len(mapping) for mapping in dict(mapping_by_type).values())


def _object_name(value: Any) -> str | None:
    name = getattr(value, "name", None)
    if name is not None:
        return str(name)
    return None if value is None else str(value)


def _qualified_type_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__name__}"


__all__ = [
    "EXPECTED_MILESTONE_8B",
    "HISTORICAL_BLOCKS_8B",
    "MATERIALIZATION_GATE_NAME",
    "MILESTONE_8B_DEPENDENCY_GRAPH",
    "MaterializationError",
    "MaterializationSafetyError",
    "assert_materialization_pre_state",
    "build_base_skeleton_for_materialization",
    "build_milestone_8b_materialization_report",
    "build_milestone_8b_unavailable_report",
    "collect_post_materialization_snapshot",
    "collect_pre_materialization_snapshot",
    "compare_milestone_8b",
    "compare_to_historical_blocks",
    "instantiate_neuromechfly",
    "materialize_joints_explicit_gate",
    "state_transition",
    "write_json_report",
]
