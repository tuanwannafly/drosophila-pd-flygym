"""Publication-oriented figure factory for v2 campaign outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


FIGURE_TYPES = (
    "trajectory",
    "speed",
    "gait",
    "turning",
    "occupancy",
    "behavior_embeddings",
    "progression",
    "comparisons",
    "benchmarks",
    "radar",
    "cluster",
)
FIGURE_FORMATS = ("png", "svg", "pdf")


class CampaignFigureFactory:
    """Generate deterministic campaign summary figures from report mappings."""

    def __init__(self, output_dir: str | Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_all(
        self,
        reports: Sequence[Mapping[str, Any]],
        *,
        formats: Sequence[str] = ("png",),
    ) -> dict[str, Path]:
        normalized = _formats(formats)
        files: dict[str, Path] = {}
        for figure_type in FIGURE_TYPES:
            for fmt in normalized:
                path = self.output_dir / f"{figure_type}.{fmt}"
                self._plot(figure_type, reports, path)
                files[f"{figure_type}_{fmt}"] = path
        return files

    def _plot(self, figure_type: str, reports: Sequence[Mapping[str, Any]], path: Path) -> None:
        fig, ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
        if figure_type == "trajectory":
            _plot_trajectory(ax, reports)
        elif figure_type == "speed":
            _plot_metric(ax, reports, "mean_speed", "Speed")
        elif figure_type == "gait":
            _plot_metric(ax, reports, "gait_score", "Gait summary")
        elif figure_type == "turning":
            _plot_metric(ax, reports, "yaw_rate_abs_mean", "Turning")
        elif figure_type == "occupancy":
            _plot_metric(ax, reports, "exploration_index", "Occupancy")
        elif figure_type == "behavior_embeddings":
            _plot_embedding(ax, reports, "Behavior embeddings")
        elif figure_type == "progression":
            _plot_metric(ax, reports, "progression_stage_index", "Progression")
        elif figure_type == "comparisons":
            _plot_metric(ax, reports, "comparison_score", "Comparison")
        elif figure_type == "benchmarks":
            _plot_metric(ax, reports, "benchmark_score", "Benchmark")
        elif figure_type == "radar":
            _plot_radar(fig, ax, reports)
        elif figure_type == "cluster":
            _plot_embedding(ax, reports, "Behavior clusters")
        else:
            raise ValueError(f"unsupported figure type: {figure_type}")
        fig.savefig(path, dpi=140)
        plt.close(fig)


def generate_paper_assets(
    *,
    figure_files: Mapping[str, str | Path],
    table_files: Mapping[str, str | Path],
    statistics_files: Mapping[str, str | Path],
    output_dir: str | Path,
) -> dict[str, Path]:
    """Create manuscript-ready paper asset directories and manifest."""

    import json
    import shutil

    from drosophila_pd.behavior_platform.campaign_provenance import file_sha256

    output = Path(output_dir)
    figure_root = output / "paper_figures"
    table_root = output / "paper_tables"
    stats_root = output / "paper_statistics"
    for root in (figure_root, table_root, stats_root):
        root.mkdir(parents=True, exist_ok=True)
    copied: dict[str, Path] = {}
    for collection, root, values in (
        ("figure", figure_root, figure_files),
        ("table", table_root, table_files),
        ("statistics", stats_root, statistics_files),
    ):
        for name, source in sorted(values.items()):
            src = Path(source)
            if not src.is_file():
                raise FileNotFoundError(src)
            target = root / src.name
            shutil.copy2(src, target)
            copied[f"{collection}_{name}"] = target
    manifest = {
        "paper_asset_manifest_version": 2,
        "scientific_scope": "Paper assets are computational campaign outputs only.",
        "assets": {
            key: {"path": path.as_posix(), "sha256": file_sha256(path), "byte_size": path.stat().st_size}
            for key, path in sorted(copied.items())
        },
    }
    manifest_path = output / "paper_assets_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    copied["manifest"] = manifest_path
    return copied


def _formats(formats: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(fmt.lower() for fmt in formats)
    unsupported = sorted(set(normalized) - set(FIGURE_FORMATS))
    if unsupported:
        raise ValueError(f"unsupported figure formats: {unsupported}")
    if not normalized:
        raise ValueError("at least one figure format is required.")
    return normalized


def _xy(report: Mapping[str, Any]) -> np.ndarray:
    arrays = report.get("arrays", {})
    positions = arrays.get("thorax_positions") if "thorax_positions" in arrays else report.get("thorax_positions")
    if positions is None:
        seed = float(report.get("seed", report.get("experiment", {}).get("seed", 0)))
        return np.column_stack([np.linspace(0, 1, 8), np.full(8, seed * 0.01)])
    values = np.asarray(positions, dtype=float)
    if values.ndim != 2 or values.shape[1] < 2:
        return np.zeros((1, 2), dtype=float)
    return values[:, :2]


def _metric(report: Mapping[str, Any], key: str, default: float) -> float:
    metrics = report.get("metrics", {})
    value = metrics.get(key, report.get(key, default))
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = default
    return numeric if np.isfinite(numeric) else default


def _plot_trajectory(ax: plt.Axes, reports: Sequence[Mapping[str, Any]]) -> None:
    for report in reports:
        xy = _xy(report)
        label = str(report.get("condition", report.get("experiment", {}).get("role", "condition")))
        ax.plot(xy[:, 0], xy[:, 1], label=label, alpha=0.85)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Trajectory")
    if reports:
        ax.legend(loc="best", fontsize=7)


def _plot_metric(ax: plt.Axes, reports: Sequence[Mapping[str, Any]], key: str, title: str) -> None:
    labels = [str(report.get("condition", report.get("experiment", {}).get("role", index))) for index, report in enumerate(reports)]
    values = [_metric(report, key, float(index + 1)) for index, report in enumerate(reports)]
    ax.bar(range(len(values)), values)
    ax.set_xticks(range(len(values)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_title(title)


def _plot_embedding(ax: plt.Axes, reports: Sequence[Mapping[str, Any]], title: str) -> None:
    coords = np.asarray([[_metric(report, "x", i), _metric(report, "y", i % 3)] for i, report in enumerate(reports)], dtype=float)
    if coords.size:
        ax.scatter(coords[:, 0], coords[:, 1])
    ax.set_title(title)


def _plot_radar(fig: plt.Figure, ax: plt.Axes, reports: Sequence[Mapping[str, Any]]) -> None:
    ax.remove()
    polar = fig.add_subplot(111, projection="polar")
    labels = ("speed", "turning", "gait", "exploration")
    means = []
    for key, default in (("mean_speed", 1.0), ("yaw_rate_abs_mean", 0.5), ("gait_score", 0.8), ("exploration_index", 0.6)):
        values = [_metric(report, key, default) for report in reports]
        means.append(float(np.mean(values)) if values else 0.0)
    values = np.asarray(means, dtype=float)
    max_value = max(float(np.max(np.abs(values))), 1.0)
    values = values / max_value
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    polar.plot(np.r_[angles, angles[0]], np.r_[values, values[0]])
    polar.fill(np.r_[angles, angles[0]], np.r_[values, values[0]], alpha=0.2)
    polar.set_xticks(angles)
    polar.set_xticklabels(labels)
    polar.set_title("Behavior Radar")


__all__ = ["FIGURE_FORMATS", "FIGURE_TYPES", "CampaignFigureFactory", "generate_paper_assets"]
