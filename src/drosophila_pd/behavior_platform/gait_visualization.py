"""Static visualizations for v2 gait-analysis outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drosophila_pd.behavior_platform.gait import GaitInput, analyze_gait


def plot_footfall_diagram(
    gait_input: GaitInput,
    analysis: Mapping[str, Any] | None,
    output_path: str | Path,
) -> Path:
    """Render stance bouts as horizontal footfall bars."""

    report = dict(analysis or analyze_gait(gait_input))
    path = _prepare_path(output_path)
    legs = report["leg_order"]
    bouts = report["contact_analysis"]["stance_bouts"]

    fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
    for row, leg in enumerate(legs):
        for bout in bouts[leg]:
            ax.broken_barh(
                [(bout["start_time_s"], bout["duration_s"])],
                (row - 0.35, 0.7),
                facecolors="#2f6f9f",
            )
    ax.set_yticks(range(len(legs)))
    ax.set_yticklabels(legs)
    ax.set_xlabel("time (s)")
    ax.set_title("Footfall Diagram")
    ax.grid(axis="x", alpha=0.25)
    return _save(fig, path)


def plot_contact_raster(
    gait_input: GaitInput,
    analysis: Mapping[str, Any] | None,
    output_path: str | Path,
) -> Path:
    """Render a binary contact raster."""

    report = dict(analysis or analyze_gait(gait_input))
    path = _prepare_path(output_path)
    raster = np.asarray(report["contact_analysis"]["contact_raster"]["samples"], dtype=float).T
    legs = report["leg_order"]

    fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
    ax.imshow(raster, aspect="auto", interpolation="nearest", cmap="Greys", origin="lower")
    ax.set_yticks(range(len(legs)))
    ax.set_yticklabels(legs)
    ax.set_xlabel("sample")
    ax.set_title("Contact Raster")
    return _save(fig, path)


def plot_gait_timeline(
    gait_input: GaitInput,
    analysis: Mapping[str, Any] | None,
    output_path: str | Path,
) -> Path:
    """Render support count and gait-pattern transitions over time."""

    report = dict(analysis or analyze_gait(gait_input))
    path = _prepare_path(output_path)
    timeline = report["contact_analysis"]["contact_timeline"]
    time_s = np.asarray([row["time_s"] for row in timeline], dtype=float)
    support = np.asarray([row["support_count"] for row in timeline], dtype=float)
    transitions = report["gait_analysis"]["gait_transition_detection"]["transitions"]

    fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
    ax.step(time_s, support, where="post", color="#1f77b4", linewidth=2)
    for transition in transitions:
        ax.axvline(transition["time_s"], color="#d62728", alpha=0.2)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("support count")
    ax.set_title("Gait Timeline")
    ax.set_ylim(-0.2, max(6.2, float(np.max(support)) + 0.5))
    return _save(fig, path)


def plot_coordination_matrix(
    gait_input: GaitInput,
    analysis: Mapping[str, Any] | None,
    output_path: str | Path,
) -> Path:
    """Render contact coactivity correlation matrix."""

    report = dict(analysis or analyze_gait(gait_input))
    path = _prepare_path(output_path)
    matrix = np.asarray(report["coordination_analysis"]["coordination_matrix"]["correlation"], dtype=float)
    legs = report["leg_order"]

    fig, ax = plt.subplots(figsize=(6, 5), constrained_layout=True)
    image = ax.imshow(matrix, vmin=-1, vmax=1, cmap="coolwarm")
    ax.set_xticks(range(len(legs)))
    ax.set_xticklabels(legs)
    ax.set_yticks(range(len(legs)))
    ax.set_yticklabels(legs)
    ax.set_title("Coordination Matrix")
    fig.colorbar(image, ax=ax, label="correlation")
    return _save(fig, path)


def plot_phase_wheel(
    gait_input: GaitInput,
    analysis: Mapping[str, Any] | None,
    output_path: str | Path,
) -> Path:
    """Render inter-leg phases on a polar wheel."""

    report = dict(analysis or analyze_gait(gait_input))
    path = _prepare_path(output_path)
    phase = report["coordination_analysis"]["inter_leg_phase"]

    fig = plt.figure(figsize=(6, 6), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    for index, (pair, values) in enumerate(sorted(phase.items())):
        samples = np.asarray(values["phase_fraction"], dtype=float)
        angles = samples * 2 * np.pi
        radii = np.full(samples.shape, 1.0 + index * 0.05)
        ax.scatter(angles, radii, s=18, label=pair)
    ax.set_title("Inter-leg Phase")
    ax.set_yticklabels([])
    if phase:
        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), fontsize=7)
    return _save(fig, path)


def plot_stride_plot(
    gait_input: GaitInput,
    analysis: Mapping[str, Any] | None,
    output_path: str | Path,
) -> Path:
    """Render per-leg stride duration distributions."""

    report = dict(analysis or analyze_gait(gait_input))
    path = _prepare_path(output_path)
    legs = report["leg_order"]
    values = [
        [event["duration_s"] for event in report["gait_analysis"]["stride_events"][leg]]
        for leg in legs
    ]

    fig, ax = plt.subplots(figsize=(8, 4), constrained_layout=True)
    ax.boxplot(values, tick_labels=legs, showmeans=True)
    ax.set_ylabel("stride duration (s)")
    ax.set_title("Stride Durations")
    return _save(fig, path)


def plot_joint_trajectories(
    gait_input: GaitInput,
    analysis: Mapping[str, Any] | None,
    output_path: str | Path,
) -> Path:
    """Render available joint trajectories."""

    _ = analysis
    path = _prepare_path(output_path)
    joints = gait_input.joint_arrays()
    time_s = gait_input.time_s()

    fig, ax = plt.subplots(figsize=(9, 4), constrained_layout=True)
    for name, values in sorted(joints.items()):
        array = np.asarray(values, dtype=float)
        series = array if array.ndim == 1 else array[:, 0]
        ax.plot(time_s, series, label=name)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("joint value")
    ax.set_title("Joint Trajectories")
    if joints:
        ax.legend(loc="best", fontsize=7)
    return _save(fig, path)


def plot_foot_trajectories(
    gait_input: GaitInput,
    analysis: Mapping[str, Any] | None,
    output_path: str | Path,
) -> Path:
    """Render available foot x/y trajectories."""

    _ = analysis
    path = _prepare_path(output_path)
    feet = gait_input.foot_arrays()

    fig, ax = plt.subplots(figsize=(6, 5), constrained_layout=True)
    for leg, values in sorted(feet.items()):
        ax.plot(values[:, 0], values[:, 1], label=leg)
        ax.scatter([values[0, 0]], [values[0, 1]], s=18)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Foot Trajectories")
    ax.axis("equal")
    if feet:
        ax.legend(loc="best", fontsize=7)
    return _save(fig, path)


def render_gait_visualization_set(
    gait_input: GaitInput,
    output_dir: str | Path,
    *,
    analysis: Mapping[str, Any] | None = None,
    formats: tuple[str, ...] = ("png",),
) -> dict[str, Path]:
    """Generate the canonical gait static-figure set."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    report = dict(analysis or analyze_gait(gait_input))
    files: dict[str, Path] = {}
    plotters = {
        "footfall": plot_footfall_diagram,
        "contact_raster": plot_contact_raster,
        "gait_timeline": plot_gait_timeline,
        "coordination_matrix": plot_coordination_matrix,
        "phase_wheel": plot_phase_wheel,
        "stride_plot": plot_stride_plot,
        "joint_trajectories": plot_joint_trajectories,
        "foot_trajectories": plot_foot_trajectories,
    }
    for fmt in formats:
        normalized = fmt.lower()
        if normalized not in {"png", "svg"}:
            raise ValueError(f"unsupported visualization format: {fmt}")
        for name, plotter in plotters.items():
            files[f"{name}_{normalized}"] = plotter(
                gait_input,
                report,
                output / f"{name}.{normalized}",
            )
    return files


def _prepare_path(output_path: str | Path) -> Path:
    path = Path(output_path)
    if path.suffix.lower() not in {".png", ".svg"}:
        raise ValueError("gait visualization output must end in .png or .svg.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _save(fig: plt.Figure, path: Path) -> Path:
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


__all__ = [
    "plot_contact_raster",
    "plot_coordination_matrix",
    "plot_foot_trajectories",
    "plot_footfall_diagram",
    "plot_gait_timeline",
    "plot_joint_trajectories",
    "plot_phase_wheel",
    "plot_stride_plot",
    "render_gait_visualization_set",
]
