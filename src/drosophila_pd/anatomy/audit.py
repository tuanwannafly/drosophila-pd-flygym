"""Non-mutating anatomy audits for the Block 8.12 checkpoint."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
import json
import platform
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_BLOCK_8_12: dict[str, Any] = {
    "python_major_minor": "3.12",
    "flygym_version": "2.1.0",
    "mujoco_version": "3.9.0",
    "fly_type": "flygym.compose.fly.neuromechfly.NeuroMechFly",
    "skeleton_before_is_none": True,
    "skeleton_after_is_none": True,
    "base_skeleton_type": "flygym.anatomy.Skeleton",
    "axis_order": "PITCH_ROLL_YAW",
    "body_segment_count": 69,
    "anatomical_joint_count": 68,
    "jointdof_count": 204,
    "axis_counts": {"pitch": 68, "roll": 68, "yaw": 68},
    "leg_jointdof_counts": {
        "LF": 24,
        "LM": 24,
        "LH": 24,
        "RF": 24,
        "RM": 24,
        "RH": 24,
    },
    "non_leg_jointdof_count": 60,
    "mjcf_body_mapping_count": 69,
    "mjcf_body_mapping_total": 69,
    "missing_parent_mjcf_body_count": 0,
    "missing_child_mjcf_body_count": 0,
    "jointdof_to_mjcfjoint_length": 0,
    "jointdof_to_neutralangle_length": 0,
    "jointdof_unique_name_count": 204,
    "jointdof_roundtrip_supported": True,
    "jointdof_roundtrip_failure_count": 0,
}

EXPECTED_ACTUATOR_TYPES = (
    "MOTOR",
    "POSITION",
    "VELOCITY",
    "INTVELOCITY",
    "DAMPER",
    "CYLINDER",
    "MUSCLE",
    "ADHESION",
    "TENDON",
)


class AuditError(RuntimeError):
    """Raised when the audit cannot collect required observations."""


class AuditSafetyError(AuditError):
    """Raised when a pre-materialization safety invariant is violated."""


def package_version(package_name: str) -> str | None:
    """Return an installed package version, or None when it is unavailable."""

    try:
        return version(package_name)
    except PackageNotFoundError:
        return None


def runtime_environment() -> dict[str, str | None]:
    """Collect runtime versions without importing FlyGym or MuJoCo."""

    return {
        "python_version": platform.python_version(),
        "python_major_minor": ".".join(platform.python_version_tuple()[:2]),
        "flygym_version": package_version("flygym"),
        "mujoco_version": package_version("mujoco"),
    }


def git_commit(repo_root: str | Path | None = None) -> str | None:
    """Return the current git commit hash when available."""

    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or None


def instantiate_neuromechfly() -> Any:
    """Instantiate the default FlyGym NeuroMechFly object.

    Imports happen inside this function so the repository can still be imported
    and tested in environments where FlyGym and MuJoCo are not installed.
    """

    module = import_module("flygym.compose.fly.neuromechfly")
    return module.NeuroMechFly()


def assert_pre_materialized(fly: Any, *, phase: str) -> None:
    """Assert that the live fly object remains in the Block 8.12 state."""

    if not hasattr(fly, "skeleton"):
        raise AuditSafetyError(f"Fly object has no skeleton attribute before {phase}.")
    if fly.skeleton is not None:
        raise AuditSafetyError(f"Expected fly.skeleton is None {phase}.")


def collect_block_8_12_observations(fly: Any) -> dict[str, Any]:
    """Collect Block 8.12 observations without materializing the skeleton."""

    assert_pre_materialized(fly, phase="before audit")
    skeleton_before_is_none = fly.skeleton is None

    if not hasattr(fly, "_get_base_skeleton"):
        raise AuditError("Fly object does not expose _get_base_skeleton.")
    if not hasattr(fly, "root_segment"):
        raise AuditError("Fly object does not expose root_segment.")

    base_skeleton = fly._get_base_skeleton()
    root_segment = fly.root_segment
    jointdofs = list(base_skeleton.iter_jointdofs(root=root_segment))
    jointdof_names = [jointdof.name for jointdof in jointdofs]

    body_segments = list(getattr(base_skeleton, "body_segments"))
    body_segment_names = {_object_name(body_segment) for body_segment in body_segments}
    bodyseg_to_mjcfbody = dict(getattr(fly, "bodyseg_to_mjcfbody", {}))
    mapped_body_segment_names = {_object_name(key) for key in bodyseg_to_mjcfbody}

    missing_body_segment_names = sorted(body_segment_names - mapped_body_segment_names)
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

    leg_counts, non_leg_count = _leg_group_counts(jointdofs)
    roundtrip = _jointdof_roundtrip_summary(jointdofs)

    assert_pre_materialized(fly, phase="after audit")
    skeleton_after_is_none = fly.skeleton is None

    return {
        **runtime_environment(),
        "fly_type": _qualified_type_name(fly),
        "skeleton_before_is_none": skeleton_before_is_none,
        "skeleton_after_is_none": skeleton_after_is_none,
        "base_skeleton_type": _qualified_type_name(base_skeleton),
        "axis_order": _enum_name(getattr(base_skeleton, "axis_order")),
        "root_segment": _object_name(root_segment),
        "body_segment_count": len(body_segments),
        "anatomical_joint_count": len(getattr(base_skeleton, "anatomical_joints")),
        "jointdof_count": len(jointdofs),
        "axis_counts": _axis_counts(jointdofs),
        "leg_jointdof_counts": leg_counts,
        "non_leg_jointdof_count": non_leg_count,
        "mjcf_body_mapping_count": len(mapped_body_segment_names),
        "mjcf_body_mapping_total": len(body_segment_names),
        "missing_mjcf_body_segment_names": missing_body_segment_names,
        "missing_parent_mjcf_body_count": len(missing_parent_names),
        "missing_parent_mjcf_body_names": missing_parent_names,
        "missing_child_mjcf_body_count": len(missing_child_names),
        "missing_child_mjcf_body_names": missing_child_names,
        "jointdof_to_mjcfjoint_length": len(
            getattr(fly, "jointdof_to_mjcfjoint", {})
        ),
        "jointdof_to_neutralangle_length": len(
            getattr(fly, "jointdof_to_neutralangle", {})
        ),
        "jointdof_to_mjcfactuator_by_type_lengths": _mapping_lengths_by_type(
            getattr(fly, "jointdof_to_mjcfactuator_by_type", {})
        ),
        "jointdof_to_neutralaction_by_type_lengths": _mapping_lengths_by_type(
            getattr(fly, "jointdof_to_neutralaction_by_type", {})
        ),
        "jointdof_unique_name_count": len(set(jointdof_names)),
        "jointdof_first_names": jointdof_names[:15],
        **roundtrip,
    }


def compare_to_expected(observed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Compare observed Block 8.12 values with the documented invariants."""

    checks: dict[str, dict[str, Any]] = {}
    for key, expected in EXPECTED_BLOCK_8_12.items():
        _add_check(checks, key, expected, observed.get(key))

    for axis, expected_count in EXPECTED_BLOCK_8_12["axis_counts"].items():
        _add_check(
            checks,
            f"axis_count_{axis}",
            expected_count,
            observed.get("axis_counts", {}).get(axis),
        )

    for leg, expected_count in EXPECTED_BLOCK_8_12["leg_jointdof_counts"].items():
        _add_check(
            checks,
            f"leg_jointdof_count_{leg}",
            expected_count,
            observed.get("leg_jointdof_counts", {}).get(leg),
        )

    _add_check(
        checks,
        "mjcf_actuator_mapping_types",
        sorted(EXPECTED_ACTUATOR_TYPES),
        sorted(observed.get("jointdof_to_mjcfactuator_by_type_lengths", {})),
    )
    _add_check(
        checks,
        "neutral_action_mapping_types",
        sorted(EXPECTED_ACTUATOR_TYPES),
        sorted(observed.get("jointdof_to_neutralaction_by_type_lengths", {})),
    )

    for actuator_type in EXPECTED_ACTUATOR_TYPES:
        _add_check(
            checks,
            f"mjcf_actuator_mapping_length_{actuator_type}",
            0,
            observed.get("jointdof_to_mjcfactuator_by_type_lengths", {}).get(
                actuator_type
            ),
        )
        _add_check(
            checks,
            f"neutral_action_mapping_length_{actuator_type}",
            0,
            observed.get("jointdof_to_neutralaction_by_type_lengths", {}).get(
                actuator_type
            ),
        )

    return checks


def build_block_8_12_report(
    fly: Any, *, repo_root: str | Path | None = None
) -> dict[str, Any]:
    """Build a JSON-serializable Block 8.12 audit report."""

    observed = collect_block_8_12_observations(fly)
    checks = compare_to_expected(observed)
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "expected_invariants": EXPECTED_BLOCK_8_12,
        "expected_actuator_types": list(EXPECTED_ACTUATOR_TYPES),
        "observed": observed,
        "checks": checks,
        "overall_pass": all(item["pass"] for item in checks.values()),
        "scientific_scope": (
            "This audit validates software/anatomy invariants only. It does not "
            "validate a Parkinson's disease model, locomotor biology, or evidence "
            "from real flies."
        ),
    }


def build_unavailable_report(
    error: BaseException, *, repo_root: str | Path | None = None
) -> dict[str, Any]:
    """Build a report for environments that cannot execute the FlyGym audit."""

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "expected_invariants": EXPECTED_BLOCK_8_12,
        "expected_actuator_types": list(EXPECTED_ACTUATOR_TYPES),
        "observed": runtime_environment(),
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
    }


def write_json_report(report: dict[str, Any], output_path: str | Path) -> None:
    """Write a small JSON audit report."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")


def _add_check(
    checks: dict[str, dict[str, Any]], name: str, expected: Any, observed: Any
) -> None:
    checks[name] = {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


def _axis_counts(jointdofs: list[Any]) -> dict[str, int]:
    counts = Counter(_enum_value(getattr(jointdof, "axis")) for jointdof in jointdofs)
    return {axis: counts.get(axis, 0) for axis in ("pitch", "roll", "yaw")}


def _leg_group_counts(jointdofs: list[Any]) -> tuple[dict[str, int], int]:
    leg_counts = {leg: 0 for leg in ("LF", "LM", "LH", "RF", "RM", "RH")}
    non_leg_count = 0

    for jointdof in jointdofs:
        child = getattr(jointdof, "child")
        if _segment_is_leg(child):
            leg = str(getattr(child, "pos")).upper()
            leg_counts[leg] = leg_counts.get(leg, 0) + 1
        else:
            non_leg_count += 1

    return leg_counts, non_leg_count


def _jointdof_roundtrip_summary(jointdofs: list[Any]) -> dict[str, Any]:
    if not jointdofs:
        return {
            "jointdof_roundtrip_supported": False,
            "jointdof_roundtrip_failure_count": None,
            "jointdof_roundtrip_failure_names": [],
        }

    from_name = getattr(type(jointdofs[0]), "from_name", None)
    if not callable(from_name):
        return {
            "jointdof_roundtrip_supported": False,
            "jointdof_roundtrip_failure_count": None,
            "jointdof_roundtrip_failure_names": [],
        }

    failures = []
    for jointdof in jointdofs:
        try:
            reconstructed = from_name(jointdof.name)
        except Exception:
            failures.append(jointdof.name)
            continue
        if reconstructed != jointdof:
            failures.append(jointdof.name)

    return {
        "jointdof_roundtrip_supported": True,
        "jointdof_roundtrip_failure_count": len(failures),
        "jointdof_roundtrip_failure_names": failures,
    }


def _mapping_lengths_by_type(mapping_by_type: Any) -> dict[str, int]:
    return {
        _enum_name(mapping_type): len(mapping)
        for mapping_type, mapping in dict(mapping_by_type).items()
    }


def _qualified_type_name(value: Any) -> str:
    cls = type(value)
    return f"{cls.__module__}.{cls.__name__}"


def _object_name(value: Any) -> str:
    return str(getattr(value, "name", value))


def _enum_name(value: Any) -> str:
    return str(getattr(value, "name", value))


def _enum_value(value: Any) -> str:
    return str(getattr(value, "value", value))


def _segment_is_leg(segment: Any) -> bool:
    is_leg = getattr(segment, "is_leg", None)
    if callable(is_leg):
        return bool(is_leg())
    return str(getattr(segment, "pos", "")).lower() in {"lf", "lm", "lh", "rf", "rm", "rh"}
