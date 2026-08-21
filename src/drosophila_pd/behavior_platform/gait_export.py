"""Export helpers for v2 gait-analysis packages."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

from drosophila_pd.behavior_platform.gait import GaitInput, analyze_gait
from drosophila_pd.behavior_platform.gait_visualization import render_gait_visualization_set


SUPPORTED_GAIT_EXPORT_FORMATS = ("csv", "json", "npz", "png", "svg")


@dataclass(frozen=True)
class GaitExportRequest:
    output_dir: Path | str
    formats: tuple[str, ...] = SUPPORTED_GAIT_EXPORT_FORMATS
    include_visualizations: bool = True
    overwrite: bool = True


@dataclass(frozen=True)
class GaitExportResult:
    output_dir: Path
    files: dict[str, Path]
    analysis: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "output_dir": str(self.output_dir),
            "files": {key: str(path) for key, path in self.files.items()},
            "analysis_included": True,
        }


def export_gait_package(
    gait_input: GaitInput,
    request: GaitExportRequest,
    *,
    analysis: Mapping[str, Any] | None = None,
) -> GaitExportResult:
    """Write a deterministic gait-analysis package in requested formats."""

    formats = _normalize_formats(request.formats)
    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    planned = _planned_files(formats, output_dir, include_visualizations=request.include_visualizations)
    if not request.overwrite:
        _reject_existing(planned.values())
    report = dict(analysis or analyze_gait(gait_input))

    files: dict[str, Path] = {}
    if "json" in formats:
        files["gait_analysis_json"] = _write_json(report, output_dir)
    if "csv" in formats:
        files.update(_write_csv_tables(report, output_dir))
    if "npz" in formats:
        files["gait_arrays_npz"] = _write_npz(gait_input, report, output_dir)
    viz_formats = tuple(fmt for fmt in formats if fmt in {"png", "svg"})
    if request.include_visualizations and viz_formats:
        files.update(
            render_gait_visualization_set(
                gait_input,
                output_dir / "figures",
                analysis=report,
                formats=viz_formats,
            )
        )
    return GaitExportResult(output_dir=output_dir, files=files, analysis=report)


def _write_json(report: Mapping[str, Any], output_dir: Path) -> Path:
    path = output_dir / "gait_analysis.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_csv_tables(report: Mapping[str, Any], output_dir: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    files["contact_timeline_csv"] = output_dir / "contact_timeline.csv"
    _write_rows(
        files["contact_timeline_csv"],
        report["contact_analysis"]["contact_timeline"],
        ["sample_index", "time_s", "active_legs", "support_count", "pattern"],
    )
    files["stride_events_csv"] = output_dir / "stride_events.csv"
    stride_rows = []
    for leg, events in report["gait_analysis"]["stride_events"].items():
        stride_rows.extend(events)
    _write_rows(
        files["stride_events_csv"],
        stride_rows,
        [
            "leg",
            "stride_index",
            "start_sample",
            "end_sample_exclusive",
            "start_time_s",
            "end_time_s",
            "duration_s",
            "frequency_hz",
            "stance_duration_s",
            "stance_fraction",
            "stride_length_mm",
        ],
    )
    files["duty_factor_csv"] = output_dir / "duty_factor.csv"
    duty_rows = [
        {"leg": leg, "duty_factor": value}
        for leg, value in report["contact_analysis"]["duty_factor_by_leg"].items()
    ]
    _write_rows(files["duty_factor_csv"], duty_rows, ["leg", "duty_factor"])
    return files


def _write_npz(gait_input: GaitInput, report: Mapping[str, Any], output_dir: Path) -> Path:
    path = output_dir / "gait_arrays.npz"
    contacts = gait_input.contact_arrays(
        threshold=float(report["configuration"]["contact_threshold"])
    )
    arrays: dict[str, np.ndarray] = {
        "time_s": gait_input.time_s(),
        "contact_matrix": np.vstack(
            [contacts[leg].astype(int) for leg in report["leg_order"]]
        ),
    }
    for leg, values in gait_input.foot_arrays().items():
        arrays[f"foot__{leg}"] = values
    for name, values in gait_input.joint_arrays().items():
        arrays[f"joint__{name}"] = values
    np.savez_compressed(path, **arrays)
    return path


def _write_rows(path: Path, rows: Iterable[Mapping[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _csv_value(row.get(key)) for key in fieldnames})


def _csv_value(value: Any) -> Any:
    if isinstance(value, (list, tuple)):
        return "|".join(str(item) for item in value)
    return value


def _normalize_formats(formats: Iterable[str]) -> tuple[str, ...]:
    normalized = tuple(str(value).lower() for value in formats)
    unsupported = sorted(set(normalized) - set(SUPPORTED_GAIT_EXPORT_FORMATS))
    if unsupported:
        raise ValueError(f"unsupported gait export formats: {unsupported}")
    if not normalized:
        raise ValueError("at least one gait export format is required.")
    return normalized


def _planned_files(
    formats: Iterable[str],
    output_dir: Path,
    *,
    include_visualizations: bool,
) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if "json" in formats:
        files["gait_analysis_json"] = output_dir / "gait_analysis.json"
    if "csv" in formats:
        files["contact_timeline_csv"] = output_dir / "contact_timeline.csv"
        files["stride_events_csv"] = output_dir / "stride_events.csv"
        files["duty_factor_csv"] = output_dir / "duty_factor.csv"
    if "npz" in formats:
        files["gait_arrays_npz"] = output_dir / "gait_arrays.npz"
    if include_visualizations:
        for fmt in formats:
            if fmt in {"png", "svg"}:
                for name in (
                    "footfall",
                    "contact_raster",
                    "gait_timeline",
                    "coordination_matrix",
                    "phase_wheel",
                    "stride_plot",
                    "joint_trajectories",
                    "foot_trajectories",
                ):
                    files[f"{name}_{fmt}"] = output_dir / "figures" / f"{name}.{fmt}"
    return files


def _reject_existing(paths: Iterable[Path]) -> None:
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        raise FileExistsError(f"gait export target already exists: {existing}")


__all__ = [
    "SUPPORTED_GAIT_EXPORT_FORMATS",
    "GaitExportRequest",
    "GaitExportResult",
    "export_gait_package",
]
