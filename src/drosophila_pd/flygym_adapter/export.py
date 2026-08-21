"""JSON, CSV, NPZ, metadata, and manifest export for recorded rollouts."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from .exceptions import RolloutExportError
from .types import ExportedRollout, ObservationFrame, RolloutData


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def export_rollout(
    rollout: RolloutData,
    output_dir: str | Path,
    *,
    prefix: str = "rollout",
) -> ExportedRollout:
    """Write one complete recorded rollout package without running simulation."""

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    files: dict[str, Path] = {}
    try:
        json_path = target / f"{prefix}.json"
        json_path.write_text(json.dumps(rollout.to_dict(), indent=2, allow_nan=False), encoding="utf-8")
        files["rollout_json"] = json_path

        csv_path = target / f"{prefix}.csv"
        _write_csv(rollout.frames, csv_path)
        files["rollout_csv"] = csv_path

        npz_path = target / f"{prefix}.npz"
        np.savez_compressed(npz_path, **_npz_arrays(rollout))
        files["rollout_npz"] = npz_path

        metadata_path = target / "metadata.json"
        metadata_path.write_text(json.dumps(_json_value(rollout.metadata), indent=2, allow_nan=False), encoding="utf-8")
        files["metadata"] = metadata_path

        manifest = {
            "schema_version": rollout.schema_version,
            "created_at": datetime.now(UTC).isoformat(),
            "frame_count": rollout.frame_count,
            "files": {},
            "metadata": _json_value(rollout.metadata),
            "scientific_scope": "Recorded FlyGym observations and software provenance only; not biological validation.",
        }
        for key, path in files.items():
            manifest["files"][key] = {
                "path": path.name,
                "byte_size": path.stat().st_size,
                "sha256": _sha256(path),
            }
        manifest_path = target / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
        files["manifest"] = manifest_path
    except (OSError, TypeError, ValueError) as exc:
        raise RolloutExportError(f"Unable to export rollout to {target}") from exc

    return ExportedRollout(
        output_dir=target.as_posix(),
        files={key: path.as_posix() for key, path in files.items()},
        manifest=manifest,
    )


def _write_csv(frames: list[ObservationFrame], path: Path) -> None:
    fields = ["timestamp_s", "step", "thorax", "com", "orientation", "body_positions", "body_orientations", "joint_positions", "joint_velocity", "joint_acceleration", "contact", "actuator"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for frame in frames:
            row = frame.to_dict()
            writer.writerow({
                key: (json.dumps(value, separators=(",", ":")) if isinstance(value, (list, dict)) else value)
                for key, value in row.items()
            })


def _npz_arrays(rollout: RolloutData) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {
        "timestamp_s": np.asarray([frame.timestamp_s for frame in rollout.frames], dtype=float),
        "step": np.asarray([frame.step for frame in rollout.frames], dtype=np.int64),
    }
    for name in ("thorax", "com", "orientation", "body_positions", "body_orientations", "joint_positions", "joint_velocity", "joint_acceleration"):
        values = [getattr(frame, name) for frame in rollout.frames]
        if values and all(value is not None for value in values):
            arrays[name] = np.stack(values)
    if "timestamp_s" in arrays:
        arrays["time_s"] = arrays["timestamp_s"].copy()
    if "thorax" in arrays:
        arrays["thorax_positions"] = arrays["thorax"].copy()
    if "orientation" in arrays:
        arrays["thorax_quaternions"] = arrays["orientation"].copy()
    for key in ("found", "forces", "torques", "positions", "normals", "tangents"):
        values = [frame.contact.get(key) if frame.contact is not None else None for frame in rollout.frames]
        if values and all(value is not None for value in values):
            arrays[f"contact_{key}"] = np.stack(values)
    actuator_keys = sorted({key for frame in rollout.frames for key in frame.actuator})
    for key in actuator_keys:
        values = [frame.actuator.get(key) for frame in rollout.frames]
        if values and all(value is not None for value in values):
            arrays[f"actuator_{key}"] = np.stack(values)
    return arrays


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["export_rollout"]
