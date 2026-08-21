"""Rollout export writers for the v2 behavioral platform."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from drosophila_pd.behavior_platform.measurement import measure_rollout_behavior
from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.behavior_platform.visualization import plot_rollout_summary
from drosophila_pd.metrics.trajectory import TRAJECTORY_CSV_COLUMNS, trajectory_csv_rows


SUPPORTED_EXPORT_FORMATS = ("csv", "json", "npz", "png")


@dataclass(frozen=True)
class ExportRequest:
    output_dir: Path | str
    formats: tuple[str, ...] = SUPPORTED_EXPORT_FORMATS
    include_measurements: bool = True
    overwrite: bool = True


@dataclass(frozen=True)
class RolloutExportResult:
    output_dir: Path
    files: dict[str, Path]
    measurements: dict[str, Any] | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "output_dir": str(self.output_dir),
            "files": {key: str(path) for key, path in self.files.items()},
            "measurements_included": self.measurements is not None,
        }


def export_rollout_package(
    rollout: RolloutData,
    request: ExportRequest,
    *,
    measurement_config: dict[str, Any] | None = None,
) -> RolloutExportResult:
    """Export one rollout in requested canonical formats."""

    formats = _normalize_formats(request.formats)
    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    planned_files = _planned_files(formats, output_dir)
    if not request.overwrite:
        _reject_existing(planned_files.values())
    measurements = (
        measure_rollout_behavior(rollout, config=measurement_config)
        if request.include_measurements
        else None
    )
    files: dict[str, Path] = {}
    if "csv" in formats:
        files["trajectory_csv"] = _write_trajectory_csv(rollout, measurements, output_dir)
    if "json" in formats:
        files["behavior_json"] = _write_json(rollout, measurements, output_dir)
    if "npz" in formats:
        files["rollout_npz"] = _write_npz(rollout, output_dir)
    if "png" in formats:
        files["summary_png"] = _write_png(rollout, measurements, output_dir)
    return RolloutExportResult(output_dir=output_dir, files=files, measurements=measurements)


def _write_trajectory_csv(
    rollout: RolloutData,
    measurements: dict[str, Any] | None,
    output_dir: Path,
) -> Path:
    trajectory = measurements["trajectory"] if measurements else measure_rollout_behavior(rollout)["trajectory"]
    path = output_dir / "trajectory.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRAJECTORY_CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(trajectory_csv_rows(trajectory))
    return path


def _write_json(
    rollout: RolloutData,
    measurements: dict[str, Any] | None,
    output_dir: Path,
) -> Path:
    path = output_dir / "behavioral_measurements.json"
    payload = {
        "rollout": rollout.as_metadata(),
        "measurements": measurements,
        "scientific_scope": (
            "Exported rollout measurements are computational post-processing "
            "artifacts only; they are not biological validation."
        ),
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_npz(rollout: RolloutData, output_dir: Path) -> Path:
    path = output_dir / "rollout_arrays.npz"
    arrays: dict[str, np.ndarray] = {
        "thorax_positions": rollout.positions_array(),
        "thorax_quaternions": rollout.quaternions_array(),
        "time_s": rollout.time_s(),
    }
    com = rollout.com_array()
    if com is not None:
        arrays["com_positions"] = com
    for name, array in rollout.joint_arrays().items():
        arrays[f"joint__{name}"] = array
    for name, array in rollout.adhesion_arrays().items():
        arrays[f"adhesion__{name}"] = array
    np.savez_compressed(path, **arrays)
    return path


def _write_png(
    rollout: RolloutData,
    measurements: dict[str, Any] | None,
    output_dir: Path,
) -> Path:
    path = output_dir / "rollout_summary.png"
    plot_rollout_summary(rollout, measurements or measure_rollout_behavior(rollout), path)
    return path


def _normalize_formats(formats: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(str(value).lower() for value in formats)
    unsupported = sorted(set(normalized) - set(SUPPORTED_EXPORT_FORMATS))
    if unsupported:
        raise ValueError(f"unsupported export formats: {unsupported}")
    if not normalized:
        raise ValueError("at least one export format is required.")
    return normalized


def _planned_files(formats: Iterable[str], output_dir: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if "csv" in formats:
        files["trajectory_csv"] = output_dir / "trajectory.csv"
    if "json" in formats:
        files["behavior_json"] = output_dir / "behavioral_measurements.json"
    if "npz" in formats:
        files["rollout_npz"] = output_dir / "rollout_arrays.npz"
    if "png" in formats:
        files["summary_png"] = output_dir / "rollout_summary.png"
    return files


def _reject_existing(paths: Iterable[Path]) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise FileExistsError(f"export target already exists: {existing}")


__all__ = [
    "SUPPORTED_EXPORT_FORMATS",
    "ExportRequest",
    "RolloutExportResult",
    "export_rollout_package",
]
