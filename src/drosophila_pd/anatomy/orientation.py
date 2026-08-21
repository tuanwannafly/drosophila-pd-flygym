"""Read-only orientation audit for the Block 8.13 checkpoint."""

from __future__ import annotations

import ast
from collections.abc import Mapping
from datetime import UTC, datetime
import inspect
from pathlib import Path
import textwrap
from typing import Any

from .audit import (
    AuditError,
    AuditSafetyError,
    git_commit,
    instantiate_neuromechfly,
    runtime_environment,
    write_json_report,
)


JOINT_RELATED_KEYWORDS = (
    "joint",
    "dof",
    "mjcf",
    "neutral",
    "actuator",
    "skeleton",
    "model",
    "xml",
)

MJCF_ROOT_CANDIDATES = (
    "mjcf_root",
    "_mjcf_root",
    "root",
    "_root",
    "model",
    "mjcf",
    "_mjcf",
)

MAPPING_CONTAINER_NAMES = (
    "bodyseg_to_mjcfbody",
    "bodyseg_to_mjcfgeom",
    "bodyseg_to_mjcfmesh",
    "jointdof_to_mjcfjoint",
    "jointdof_to_mjcfactuator_by_type",
    "jointdof_to_neutralangle",
    "jointdof_to_neutralaction_by_type",
    "anatomicaljoint_to_mjcfsites",
    "leg_to_adhesionactuator",
    "sensorname_to_mjcfsensor",
    "cameraname_to_mjcfcamera",
    "eyecameraname_to_mjcfcamera",
)

EXPECTED_BLOCK_8_13_ORIENTATION: dict[str, Any] = {
    "python_major_minor": "3.12",
    "flygym_version": "2.1.0",
    "mujoco_version": "3.9.0",
    "fly_type": "flygym.compose.fly.neuromechfly.NeuroMechFly",
    "mro_contains_basefly": True,
    "skeleton_before_is_none": True,
    "skeleton_after_is_none": True,
    "mjcf_root_available": True,
    "add_joints_found": True,
    "add_joints_signature_available": True,
    "add_joints_source_location_available": True,
    "add_joints_source_available": True,
    "add_joints_changes_self_skeleton": True,
    "add_joints_creates_mjcf_joints": True,
    "add_joints_populates_joint_mappings": True,
    "add_joints_populates_neutral_angle_mapping": True,
    "add_joints_rebuilds_neutral_keyframes": True,
    "bodyseg_to_mjcfbody_length": 69,
    "jointdof_to_mjcfjoint_length": 0,
    "jointdof_to_neutralangle_length": 0,
    "jointdof_to_mjcfactuator_by_type_total_length": 0,
    "jointdof_to_neutralaction_by_type_total_length": 0,
}


class OrientationError(AuditError):
    """Raised when Block 8.13 orientation cannot be collected."""


class OrientationSafetyError(AuditSafetyError):
    """Raised when a read-only Block 8.13 safety invariant is violated."""


def assert_orientation_pre_materialized(fly: Any, *, phase: str) -> None:
    """Assert that the live fly object is still before joint materialization."""

    if not hasattr(fly, "skeleton"):
        raise OrientationSafetyError(
            f"Fly object has no skeleton attribute {phase} Block 8.13."
        )
    if fly.skeleton is not None:
        raise OrientationSafetyError(
            f"Expected fly.skeleton is None {phase} Block 8.13."
        )


def collect_block_8_13_orientation(fly: Any) -> dict[str, Any]:
    """Collect read-only Block 8.13 orientation observations.

    This function deliberately inspects signatures, source text, attributes, and
    container lengths. It never calls `add_joints()`, creates actuators, or
    intentionally mutates MJCF.
    """

    assert_orientation_pre_materialized(fly, phase="before")
    skeleton_before = _attribute_state(fly, "skeleton")

    fly_cls = type(fly)
    fly_mro = [_qualified_class_name(cls) for cls in inspect.getmro(fly_cls)]
    mapping_containers = {
        name: mapping_container_summary(name, getattr(fly, name))
        for name in MAPPING_CONTAINER_NAMES
        if hasattr(fly, name)
    }
    root_objects = mjcf_root_objects(fly)
    add_joints = add_joints_orientation(fly)

    assert_orientation_pre_materialized(fly, phase="after")
    skeleton_after = _attribute_state(fly, "skeleton")

    return {
        **runtime_environment(),
        "fly_type": _qualified_class_name(fly_cls),
        "fly_class": {
            "module": getattr(fly_cls, "__module__", None),
            "qualname": getattr(fly_cls, "__qualname__", None),
            "name": getattr(fly_cls, "__name__", None),
        },
        "fly_mro": fly_mro,
        "mro_contains_basefly": any(name.endswith(".BaseFly") for name in fly_mro),
        "joint_related_methods": joint_related_methods(fly),
        "skeleton_before": skeleton_before,
        "skeleton_after": skeleton_after,
        "skeleton_before_is_none": skeleton_before["is_none"],
        "skeleton_after_is_none": skeleton_after["is_none"],
        "mjcf_root_objects": root_objects,
        "mjcf_root_object_names": [
            item["name"] for item in root_objects if item["present"]
        ],
        "mjcf_root_available": any(
            item["name"] == "mjcf_root" and item["present"]
            for item in root_objects
        ),
        "mapping_containers": mapping_containers,
        "mapping_container_names": sorted(mapping_containers),
        "bodyseg_to_mjcfbody_length": _mapping_length(
            mapping_containers, "bodyseg_to_mjcfbody"
        ),
        "jointdof_to_mjcfjoint_length": _mapping_length(
            mapping_containers, "jointdof_to_mjcfjoint"
        ),
        "jointdof_to_neutralangle_length": _mapping_length(
            mapping_containers, "jointdof_to_neutralangle"
        ),
        "jointdof_to_mjcfactuator_by_type_total_length": _mapping_nested_total(
            mapping_containers, "jointdof_to_mjcfactuator_by_type"
        ),
        "jointdof_to_neutralaction_by_type_total_length": _mapping_nested_total(
            mapping_containers, "jointdof_to_neutralaction_by_type"
        ),
        "add_joints": add_joints,
        "add_joints_found": add_joints["found"],
        "add_joints_signature_available": add_joints["signature"] is not None,
        "add_joints_source_location_available": (
            add_joints["source_file"] is not None
            and add_joints["source_start_line"] is not None
        ),
        "add_joints_source_available": add_joints["source_available"],
        "add_joints_changes_self_skeleton": add_joints["source_facts"][
            "changes_self_skeleton"
        ],
        "add_joints_creates_mjcf_joints": add_joints["source_facts"][
            "creates_mjcf_joints"
        ],
        "add_joints_populates_joint_mappings": add_joints["source_facts"][
            "populates_joint_mappings"
        ],
        "add_joints_populates_neutral_angle_mapping": add_joints["source_facts"][
            "populates_neutral_angle_mapping"
        ],
        "add_joints_rebuilds_neutral_keyframes": add_joints["source_facts"][
            "rebuilds_neutral_keyframes"
        ],
    }


def build_block_8_13_orientation_report(
    fly: Any, *, repo_root: str | Path | None = None
) -> dict[str, Any]:
    """Build a JSON-serializable Block 8.13 orientation report."""

    observed = collect_block_8_13_orientation(fly)
    checks = compare_block_8_13_orientation(observed)
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "expected_orientation": EXPECTED_BLOCK_8_13_ORIENTATION,
        "observed": observed,
        "checks": checks,
        "overall_pass": all(item["pass"] for item in checks.values()),
        "scientific_scope": (
            "This read-only audit orients the software materialization boundary. "
            "It does not materialize joints, create actuators, mutate MJCF, or "
            "validate a Parkinson's disease model."
        ),
    }


def build_block_8_13_unavailable_report(
    error: BaseException, *, repo_root: str | Path | None = None
) -> dict[str, Any]:
    """Build a report for environments that cannot run the orientation audit."""

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "expected_orientation": EXPECTED_BLOCK_8_13_ORIENTATION,
        "observed": runtime_environment(),
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
        "scientific_scope": (
            "This read-only audit orients the software materialization boundary. "
            "It does not materialize joints, create actuators, mutate MJCF, or "
            "validate a Parkinson's disease model."
        ),
    }


def compare_block_8_13_orientation(
    observed: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Compare observed Block 8.13 orientation values to expected facts."""

    checks: dict[str, dict[str, Any]] = {}
    for key, expected in EXPECTED_BLOCK_8_13_ORIENTATION.items():
        _add_check(checks, key, expected, observed.get(key))
    return checks


def joint_related_methods(fly: Any) -> list[dict[str, Any]]:
    """Return read-only signatures for joint/MJCF/mapping-related callables."""

    methods = []
    for name in sorted(set(dir(fly))):
        if not _is_joint_related_name(name):
            continue
        try:
            value = getattr(fly, name)
        except Exception as exc:
            methods.append(
                {
                    "name": name,
                    "visibility": _visibility(name),
                    "read_error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        if not callable(value):
            continue

        signature = None
        signature_error = None
        try:
            signature = str(inspect.signature(value))
        except Exception as exc:
            signature_error = f"{type(exc).__name__}: {exc}"

        doc = inspect.getdoc(value)
        owner = _method_owner(type(fly), name)
        methods.append(
            {
                "name": name,
                "visibility": _visibility(name),
                "type": _qualified_type_name(value),
                "owner": _qualified_class_name(owner) if owner is not None else None,
                "signature": signature,
                "signature_error": signature_error,
                "docstring_first_line": _first_doc_line(doc),
            }
        )
    return methods


def mjcf_root_objects(fly: Any) -> list[dict[str, Any]]:
    """Return available MJCF/root/model object attributes without compiling."""

    objects = []
    for name in MJCF_ROOT_CANDIDATES:
        state = _attribute_state(fly, name)
        objects.append(
            {
                "name": name,
                "present": state["present"],
                "type": state["type"],
                "is_none": state["is_none"],
                "repr": state["repr"],
                "read_error": state["read_error"],
            }
        )
    return objects


def mapping_container_summary(name: str, value: Any) -> dict[str, Any]:
    """Return a JSON-safe mapping/container length summary."""

    length = _safe_len(value)
    summary: dict[str, Any] = {
        "name": name,
        "type": _qualified_type_name(value),
        "length": length,
        "nested_lengths": None,
        "nested_total_length": None,
    }
    if isinstance(value, Mapping):
        nested_lengths = {
            _stable_key_name(key): _safe_len(nested_value)
            for key, nested_value in value.items()
        }
        summary["nested_lengths"] = nested_lengths
        summary["nested_total_length"] = sum(
            nested_length
            for nested_length in nested_lengths.values()
            if isinstance(nested_length, int)
        )
    return summary


def add_joints_orientation(fly: Any) -> dict[str, Any]:
    """Inspect the `add_joints` API and source without calling it."""

    if not hasattr(fly, "add_joints"):
        return {
            "found": False,
            "owner": None,
            "signature": None,
            "owner_signature": None,
            "docstring_first_line": None,
            "source_file": None,
            "source_start_line": None,
            "source_available": False,
            "source_error": None,
            "source_facts": inspect_add_joints_source_text(None),
        }

    method = getattr(fly, "add_joints")
    owner = _method_owner(type(fly), "add_joints")
    source_target = owner.__dict__["add_joints"] if owner is not None else method

    signature = _signature_or_none(method)
    owner_signature = _signature_or_none(source_target)
    source_file = _source_file_or_none(source_target)
    source_start_line = _source_start_line_or_none(source_target)
    source_text = None
    source_error = None
    try:
        source_text = inspect.getsource(source_target)
    except Exception as exc:
        source_error = f"{type(exc).__name__}: {exc}"

    return {
        "found": True,
        "owner": _qualified_class_name(owner) if owner is not None else None,
        "signature": signature,
        "owner_signature": owner_signature,
        "docstring_first_line": _first_doc_line(inspect.getdoc(method)),
        "source_file": source_file,
        "source_start_line": source_start_line,
        "source_available": source_text is not None,
        "source_error": source_error,
        "source_facts": inspect_add_joints_source_text(source_text),
    }


def inspect_add_joints_source_text(source_text: str | None) -> dict[str, Any]:
    """Extract materialization-boundary facts from `add_joints` source text."""

    facts: dict[str, Any] = {
        "changes_self_skeleton": False,
        "creates_mjcf_joints": False,
        "populates_joint_mappings": False,
        "populates_neutral_angle_mapping": False,
        "rebuilds_neutral_keyframes": False,
        "parse_error": None,
    }
    if source_text is None:
        return facts

    try:
        tree = ast.parse(textwrap.dedent(source_text))
    except SyntaxError as exc:
        facts["parse_error"] = f"{type(exc).__name__}: {exc}"
        return facts

    facts["changes_self_skeleton"] = _has_self_attribute_assignment(tree, "skeleton")
    facts["creates_mjcf_joints"] = _has_method_call(tree, "add_joint")
    facts["populates_joint_mappings"] = _has_self_mapping_mutation(
        tree, "jointdof_to_mjcfjoint"
    )
    facts["populates_neutral_angle_mapping"] = _has_self_mapping_mutation(
        tree, "jointdof_to_neutralangle"
    )
    facts["rebuilds_neutral_keyframes"] = _has_method_call(
        tree, "_rebuild_neutral_keyframe"
    )
    return facts


def _add_check(
    checks: dict[str, dict[str, Any]], name: str, expected: Any, observed: Any
) -> None:
    checks[name] = {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


def _attribute_state(obj: Any, name: str) -> dict[str, Any]:
    try:
        value = getattr(obj, name)
    except Exception as exc:
        return {
            "present": False,
            "type": None,
            "is_none": None,
            "repr": None,
            "read_error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "present": True,
        "type": _qualified_type_name(value),
        "is_none": value is None,
        "repr": _safe_repr(value),
        "read_error": None,
    }


def _first_doc_line(doc: str | None) -> str | None:
    if not doc:
        return None
    lines = [line.strip() for line in doc.splitlines() if line.strip()]
    return lines[0] if lines else None


def _has_method_call(tree: ast.AST, method_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == method_name:
                return True
    return False


def _has_self_attribute_assignment(tree: ast.AST, attr_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(_is_self_attribute_target(target, attr_name) for target in node.targets):
                return True
        elif isinstance(node, ast.AnnAssign):
            if _is_self_attribute_target(node.target, attr_name):
                return True
        elif isinstance(node, ast.AugAssign):
            if _is_self_attribute_target(node.target, attr_name):
                return True
    return False


def _has_self_mapping_mutation(tree: ast.AST, attr_name: str) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if any(_is_self_mapping_target(target, attr_name) for target in node.targets):
                return True
        elif isinstance(node, ast.AnnAssign):
            if _is_self_mapping_target(node.target, attr_name):
                return True
        elif isinstance(node, ast.AugAssign):
            if _is_self_mapping_target(node.target, attr_name):
                return True
        elif isinstance(node, ast.Call) and _is_self_mapping_update(node, attr_name):
            return True
    return False


def _is_self_attribute_target(node: ast.AST, attr_name: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == attr_name
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    )


def _is_self_mapping_target(node: ast.AST, attr_name: str) -> bool:
    if _is_self_attribute_target(node, attr_name):
        return True
    return isinstance(node, ast.Subscript) and _is_self_attribute_target(
        node.value, attr_name
    )


def _is_self_mapping_update(node: ast.Call, attr_name: str) -> bool:
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and func.attr == "update"
        and _is_self_attribute_target(func.value, attr_name)
    )


def _is_joint_related_name(name: str) -> bool:
    lower_name = name.lower()
    return any(keyword in lower_name for keyword in JOINT_RELATED_KEYWORDS)


def _mapping_length(
    mapping_containers: dict[str, dict[str, Any]], name: str
) -> int | None:
    summary = mapping_containers.get(name)
    return None if summary is None else summary["length"]


def _mapping_nested_total(
    mapping_containers: dict[str, dict[str, Any]], name: str
) -> int | None:
    summary = mapping_containers.get(name)
    return None if summary is None else summary["nested_total_length"]


def _method_owner(cls: type[Any], method_name: str) -> type[Any] | None:
    for candidate in inspect.getmro(cls):
        if method_name in candidate.__dict__:
            return candidate
    return None


def _qualified_class_name(cls: type[Any] | None) -> str | None:
    if cls is None:
        return None
    return f"{cls.__module__}.{cls.__qualname__}"


def _qualified_type_name(value: Any) -> str:
    if isinstance(value, type):
        return _qualified_class_name(value) or "builtins.type"
    cls = type(value)
    return f"{cls.__module__}.{cls.__qualname__}"


def _safe_len(value: Any) -> int | None:
    try:
        return len(value)
    except TypeError:
        return None


def _safe_repr(value: Any, *, limit: int = 180) -> str:
    text = repr(value)
    return text if len(text) <= limit else f"{text[:limit]}..."


def _signature_or_none(value: Any) -> str | None:
    try:
        return str(inspect.signature(value))
    except Exception:
        return None


def _source_file_or_none(value: Any) -> str | None:
    try:
        return inspect.getsourcefile(value) or inspect.getfile(value)
    except Exception:
        return None


def _source_start_line_or_none(value: Any) -> int | None:
    try:
        return inspect.getsourcelines(value)[1]
    except Exception:
        return None


def _stable_key_name(key: Any) -> str:
    if hasattr(key, "name"):
        name = getattr(key, "name")
        if isinstance(name, str):
            return name
    if hasattr(key, "value"):
        value = getattr(key, "value")
        if isinstance(value, str):
            return value
    return str(key)


def _visibility(name: str) -> str:
    return "private" if name.startswith("_") else "public"


__all__ = [
    "EXPECTED_BLOCK_8_13_ORIENTATION",
    "JOINT_RELATED_KEYWORDS",
    "MAPPING_CONTAINER_NAMES",
    "MJCF_ROOT_CANDIDATES",
    "OrientationError",
    "OrientationSafetyError",
    "add_joints_orientation",
    "assert_orientation_pre_materialized",
    "build_block_8_13_orientation_report",
    "build_block_8_13_unavailable_report",
    "collect_block_8_13_orientation",
    "compare_block_8_13_orientation",
    "inspect_add_joints_source_text",
    "instantiate_neuromechfly",
    "joint_related_methods",
    "mapping_container_summary",
    "write_json_report",
]
