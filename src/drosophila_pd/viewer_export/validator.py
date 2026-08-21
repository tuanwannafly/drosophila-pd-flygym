"""Validation for generated viewer pose documents."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
from typing import Any, Mapping, Sequence

import numpy as np

from .schema import VIEWER_POSE_SCHEMA


REQUIRED_TOP_LEVEL = ("metadata", "fps", "frame_count", "joint_names", "frames")
REQUIRED_FRAME = tuple(VIEWER_POSE_SCHEMA["properties"]["frames"]["items"]["required"])


class PoseValidationError(ValueError):
    """Raised when a viewer pose document fails an integrity check."""

    def __init__(self, report: "ValidationReport") -> None:
        self.report = report
        failed = ", ".join(name for name, check in report.checks.items() if not check["pass"])
        super().__init__(f"Viewer pose validation failed: {failed}")


@dataclass(frozen=True)
class ValidationReport:
    """Machine-readable validation result for a viewer pose document."""

    overall_pass: bool
    checks: Mapping[str, Mapping[str, Any]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "overall_pass": self.overall_pass,
            "checks": {name: dict(value) for name, value in self.checks.items()},
            "scientific_scope": (
                "Read-only conversion and integrity checks for imported rollout data; "
                "no biological validation claim."
            ),
        }


def validate_pose_document(
    document: Mapping[str, Any],
    *,
    expected_frame_count: int | None = None,
    raise_on_error: bool = True,
) -> ValidationReport:
    """Validate structure, frame alignment, finite values and quaternions."""

    checks: dict[str, dict[str, Any]] = {}
    is_mapping = isinstance(document, Mapping)
    checks["top_level_fields"] = {
        "pass": is_mapping and all(field in document for field in REQUIRED_TOP_LEVEL),
        "missing": [] if not is_mapping else [field for field in REQUIRED_TOP_LEVEL if field not in document],
    }
    frames = document.get("frames", []) if is_mapping else []
    frames = frames if isinstance(frames, Sequence) and not isinstance(frames, (str, bytes)) else []
    observed_count = len(frames)
    declared_count = document.get("frame_count") if is_mapping else None
    count_pass = isinstance(declared_count, int) and observed_count == declared_count
    if expected_frame_count is not None:
        count_pass = count_pass and observed_count == int(expected_frame_count)
    checks["frame_count"] = {
        "pass": count_pass,
        "declared": declared_count,
        "observed": observed_count,
        "expected_source_count": expected_frame_count,
    }
    checks["frame_fields"] = {
        "pass": all(isinstance(frame, Mapping) and all(field in frame for field in REQUIRED_FRAME) for frame in frames),
        "missing": _missing_frame_fields(frames),
    }
    mesh = document.get("mesh") if is_mapping else None
    mesh_failures = _mesh_failures(mesh)
    checks["mesh_metadata"] = {
        "pass": not mesh_failures,
        "failures": mesh_failures,
    }
    indices = [frame.get("frame_index") for frame in frames if isinstance(frame, Mapping)]
    checks["frame_indices"] = {
        "pass": indices == list(range(observed_count)),
        "observed": indices,
    }
    frame_time_failures = _frame_time_failures(frames)
    checks["frame_times_increasing"] = {
        "pass": observed_count > 0 and not frame_time_failures,
        "failures": frame_time_failures,
    }
    finite, nan_paths, inf_paths = _finite_paths(document)
    checks["finite_values"] = {"pass": finite, "invalid_paths": sorted(set(nan_paths + inf_paths))}
    checks["no_nan"] = {"pass": not nan_paths, "paths": sorted(nan_paths)}
    checks["no_inf"] = {"pass": not inf_paths, "paths": sorted(inf_paths)}
    quaternion_paths = []
    quaternion_failures = []
    for index, frame in enumerate(frames):
        value = frame.get("orientation") if isinstance(frame, Mapping) else None
        quaternion_paths.append(index)
        try:
            quaternion = np.asarray(value, dtype=float)
            norm = float(np.linalg.norm(quaternion))
            if quaternion.shape != (4,) or not math.isfinite(norm) or not math.isclose(norm, 1.0, abs_tol=1e-6):
                quaternion_failures.append({"frame": index, "norm": norm})
        except (TypeError, ValueError):
            quaternion_failures.append({"frame": index, "norm": None})
    checks["quaternion_normalized"] = {
        "pass": not quaternion_failures and len(quaternion_paths) == observed_count,
        "failures": quaternion_failures,
    }
    trajectory_failures = []
    for index, frame in enumerate(frames):
        trajectory = frame.get("trajectory") if isinstance(frame, Mapping) else None
        thorax = trajectory.get("thorax") if isinstance(trajectory, Mapping) else None
        if not isinstance(trajectory, Mapping) or not _finite_vector(thorax, 3):
            trajectory_failures.append(index)
    checks["trajectory_complete"] = {
        "pass": observed_count > 0 and not trajectory_failures,
        "failed_frames": trajectory_failures,
    }
    report = ValidationReport(all(bool(check["pass"]) for check in checks.values()), checks)
    if raise_on_error and not report.overall_pass:
        raise PoseValidationError(report)
    return report


def _mesh_failures(mesh: Any) -> list[str]:
    failures = []
    if not isinstance(mesh, Mapping):
        return ["mesh must be an object"]
    for field in ("renderer", "render_mode", "scientific_mesh", "visibility"):
        if field not in mesh:
            failures.append(f"missing {field}")
    if "renderer" in mesh and not isinstance(mesh["renderer"], str):
        failures.append("renderer must be a string")
    if "render_mode" in mesh and not isinstance(mesh["render_mode"], str):
        failures.append("render_mode must be a string")
    if "scientific_mesh" in mesh and not isinstance(mesh["scientific_mesh"], bool):
        failures.append("scientific_mesh must be a boolean")
    if not isinstance(mesh.get("visibility"), Mapping):
        failures.append("visibility must be an object")
    if mesh.get("render_mode") == "procedural_fallback" and mesh.get("scientific_mesh") is True:
        failures.append("procedural fallback must not claim scientific_mesh")
    return failures


def _missing_frame_fields(frames: Sequence[Any]) -> list[dict[str, Any]]:
    missing = []
    for index, frame in enumerate(frames):
        if not isinstance(frame, Mapping):
            missing.append({"frame": index, "fields": list(REQUIRED_FRAME)})
            continue
        fields = [field for field in REQUIRED_FRAME if field not in frame]
        if fields:
            missing.append({"frame": index, "fields": fields})
    return missing


def _frame_time_failures(frames: Sequence[Any]) -> list[dict[str, Any]]:
    failures = []
    previous: float | None = None
    for index, frame in enumerate(frames):
        try:
            value = float(frame.get("time") if isinstance(frame, Mapping) else None)
        except (TypeError, ValueError):
            failures.append({"frame": index, "time": None, "reason": "not numeric"})
            continue
        if not math.isfinite(value) or value < 0:
            failures.append({"frame": index, "time": value, "reason": "not finite non-negative"})
        elif previous is not None and value <= previous:
            failures.append({"frame": index, "time": value, "reason": "not strictly increasing"})
        previous = value
    return failures


def _finite_paths(value: Any, path: str = "$") -> tuple[bool, list[str], list[str]]:
    nan_paths: list[str] = []
    inf_paths: list[str] = []
    if value is None or isinstance(value, (str, bool)):
        return True, nan_paths, inf_paths
    if isinstance(value, Real):
        numeric = float(value)
        if math.isnan(numeric):
            nan_paths.append(path)
        elif math.isinf(numeric):
            inf_paths.append(path)
        return not (math.isnan(numeric) or math.isinf(numeric)), nan_paths, inf_paths
    if isinstance(value, Mapping):
        for key, item in value.items():
            _, child_nan, child_inf = _finite_paths(item, f"{path}.{key}")
            nan_paths.extend(child_nan)
            inf_paths.extend(child_inf)
    elif isinstance(value, Sequence) or isinstance(value, np.ndarray):
        for index, item in enumerate(value):
            _, child_nan, child_inf = _finite_paths(item, f"{path}[{index}]")
            nan_paths.extend(child_nan)
            inf_paths.extend(child_inf)
    return not nan_paths and not inf_paths, nan_paths, inf_paths


def _finite_vector(value: Any, width: int) -> bool:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError):
        return False
    return array.shape == (width,) and bool(np.isfinite(array).all())


__all__ = ["PoseValidationError", "ValidationReport", "validate_pose_document"]
