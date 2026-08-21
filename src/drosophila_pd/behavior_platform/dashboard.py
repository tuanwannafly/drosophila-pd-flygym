"""Interactive dashboard and static export helpers for Session07/08."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drosophila_pd.behavior_platform.data_model import BehaviorDashboard
from drosophila_pd.behavior_platform.rollout import RolloutData


DASHBOARD_EXPORT_FORMATS = ("png", "svg", "pdf", "html")


def build_behavior_dashboard(
    reports: Mapping[str, Mapping[str, Any]],
    *,
    dashboard_id: str = "session07_session08_behavior_dashboard",
) -> dict[str, Any]:
    """Build a serializable dashboard specification without opening a UI."""

    dashboard = BehaviorDashboard(
        dashboard_id=dashboard_id,
        panels=(
            "trajectory_explorer",
            "occupancy_heatmap",
            "behavior_timeline",
            "progression_timeline",
            "behavior_radar",
            "parallel_coordinates",
        ),
        filters={
            "condition_selector": sorted(reports),
            "time_slider": True,
            "interactive_filtering": True,
            "camera_presets": ["top", "side", "follow"],
        },
        exports={fmt: f"{dashboard_id}.{fmt}" for fmt in DASHBOARD_EXPORT_FORMATS},
        metadata={
            "scientific_scope": "Computational behavior dashboard only.",
            "condition_count": len(reports),
        },
    )
    return {
        "dashboard_version": 2,
        "dashboard": dashboard.as_dict(),
        "reports": {name: _report_summary(report) for name, report in reports.items()},
    }


def export_behavior_dashboard(
    reports: Mapping[str, Mapping[str, Any]],
    output_dir: str | Path,
    *,
    formats: tuple[str, ...] = DASHBOARD_EXPORT_FORMATS,
) -> dict[str, Path]:
    """Export dashboard figures in PNG, SVG, PDF, and HTML."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    normalized = tuple(fmt.lower() for fmt in formats)
    unsupported = sorted(set(normalized) - set(DASHBOARD_EXPORT_FORMATS))
    if unsupported:
        raise ValueError(f"unsupported dashboard export formats: {unsupported}")
    spec = build_behavior_dashboard(reports)
    files: dict[str, Path] = {}
    for fmt in normalized:
        path = output / f"behavior_dashboard.{fmt}"
        if fmt == "html":
            path.write_text(_dashboard_html(spec), encoding="utf-8")
        else:
            _dashboard_figure(reports, path)
        files[fmt] = path
    return files


def plot_trajectory_explorer(
    rollouts: Mapping[str, RolloutData],
    output_path: str | Path,
) -> Path:
    """Render a trajectory explorer summary for several conditions."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 6), constrained_layout=True)
    for name, rollout in rollouts.items():
        xy = rollout.positions_array()[:, :2]
        ax.plot(xy[:, 0], xy[:, 1], label=name, linewidth=2)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Trajectory Explorer")
    ax.legend(loc="best")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def _dashboard_figure(reports: Mapping[str, Mapping[str, Any]], output_path: Path) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10, 8), constrained_layout=True)
    names = list(reports)
    center = [float(reports[name].get("center_occupancy", 0.0) or 0.0) for name in names]
    border = [float(reports[name].get("border_occupancy", 0.0) or 0.0) for name in names]
    entropy = [float(reports[name].get("exploration_entropy_bits", 0.0) or 0.0) for name in names]
    coverage = [float(reports[name].get("coverage_ratio", 0.0) or 0.0) for name in names]

    axes[0, 0].bar(names, center, label="center")
    axes[0, 0].bar(names, border, bottom=center, label="border")
    axes[0, 0].set_title("Occupancy")
    axes[0, 0].tick_params(axis="x", rotation=25)
    axes[0, 0].legend()

    axes[0, 1].plot(names, entropy, marker="o")
    axes[0, 1].set_title("Exploration Entropy")
    axes[0, 1].tick_params(axis="x", rotation=25)

    angles = np.linspace(0, 2 * np.pi, 4, endpoint=False)
    radar = np.vstack([center, border, entropy, coverage]).T
    for row, name in zip(radar, names):
        closed = np.r_[row, row[0]]
        axes[1, 0].plot(np.r_[angles, angles[0]], closed, label=name)
    axes[1, 0].set_title("Behavior Radar")
    axes[1, 0].legend(fontsize=7)

    for values, label in ((center, "center"), (border, "border"), (coverage, "coverage")):
        axes[1, 1].plot(names, values, marker="o", label=label)
    axes[1, 1].set_title("Parallel Coordinates")
    axes[1, 1].tick_params(axis="x", rotation=25)
    axes[1, 1].legend()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def _dashboard_html(spec: Mapping[str, Any]) -> str:
    conditions = ", ".join(spec["dashboard"]["filters"]["condition_selector"])
    panels = "".join(f"<li>{panel}</li>" for panel in spec["dashboard"]["panels"])
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<title>Behavior Dashboard</title></head><body>"
        "<h1>Behavior Dashboard</h1>"
        f"<p>Conditions: {conditions}</p>"
        "<h2>Panels</h2><ul>"
        f"{panels}</ul>"
        "<p>Computational visualization only; no biological validation claim.</p>"
        "</body></html>"
    )


def _report_summary(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "center_occupancy": report.get("center_occupancy"),
        "border_occupancy": report.get("border_occupancy"),
        "exploration_entropy_bits": report.get("exploration_entropy_bits"),
        "coverage_ratio": report.get("coverage_ratio"),
    }


__all__ = [
    "DASHBOARD_EXPORT_FORMATS",
    "build_behavior_dashboard",
    "export_behavior_dashboard",
    "plot_trajectory_explorer",
]
