"""Advanced visualization exports for Session09/10 reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


VISUAL_EXPORT_FORMATS = ("png", "svg", "pdf", "html")


def export_advanced_visualization_set(
    *,
    state_report: Mapping[str, Any],
    intervention_report: Mapping[str, Any],
    similarity_report: Mapping[str, Any],
    output_dir: str | Path,
    formats: Sequence[str] = VISUAL_EXPORT_FORMATS,
) -> dict[str, Path]:
    """Export the canonical Session09/10 advanced visualization set."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    normalized = _formats(formats)
    plotters = {
        "behavioral_state_timeline": lambda path: plot_behavioral_state_timeline(state_report, path),
        "intervention_timeline": lambda path: plot_intervention_timeline(intervention_report, path),
        "radar_plot": lambda path: plot_radar_plot(_radar_metrics(similarity_report), path),
        "sankey_transition_diagram": lambda path: plot_sankey_transition_diagram(state_report, path),
        "behavioral_network_graph": lambda path: plot_behavioral_network_graph(state_report, path),
        "trajectory_clusters": lambda path: plot_trajectory_clusters(similarity_report, path),
        "progression_map": lambda path: plot_progression_map(intervention_report, path),
        "similarity_heatmap": lambda path: plot_similarity_heatmap(similarity_report, path),
        "behavioral_embeddings": lambda path: plot_behavioral_embeddings(similarity_report, path),
        "replay_dashboard": lambda path: export_replay_dashboard(similarity_report, path),
    }
    files: dict[str, Path] = {}
    for name, plotter in plotters.items():
        for fmt in normalized:
            path = output / f"{name}.{fmt}"
            plotter(path)
            files[f"{name}_{fmt}"] = path
    return files


def plot_behavioral_state_timeline(state_report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Behavioral State Timeline", state_report)
    timeline = state_report.get("timeline", [])
    states = state_report.get("states", sorted({row["state"] for row in timeline}))
    index = {state: pos for pos, state in enumerate(states)}
    fig, ax = plt.subplots(figsize=(9, 3), constrained_layout=True)
    ax.step([row["time_s"] for row in timeline], [index[row["state"]] for row in timeline], where="post")
    ax.set_yticks(range(len(states)))
    ax.set_yticklabels(states)
    ax.set_xlabel("time (s)")
    ax.set_title("Behavioral State Timeline")
    return _save(fig, path)


def plot_intervention_timeline(intervention_report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Intervention Timeline", intervention_report)
    rows = intervention_report.get("replay", [])
    stages = sorted({row["stage_name"] for row in rows}) or ["none"]
    stage_index = {stage: index for index, stage in enumerate(stages)}
    fig, ax = plt.subplots(figsize=(9, 3), constrained_layout=True)
    ax.step([row["time_s"] for row in rows], [stage_index[row["stage_name"]] for row in rows], where="post")
    ax.set_yticks(range(len(stages)))
    ax.set_yticklabels(stages)
    ax.set_xlabel("time (s)")
    ax.set_title("Computational Intervention Timeline")
    return _save(fig, path)


def plot_radar_plot(metrics: Mapping[str, float], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Behavior Radar Plot", metrics)
    labels = list(metrics) or ["metric"]
    values = np.asarray([float(metrics[label]) for label in labels] or [0.0], dtype=float)
    angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False)
    fig = plt.figure(figsize=(5, 5), constrained_layout=True)
    ax = fig.add_subplot(111, projection="polar")
    ax.plot(np.r_[angles, angles[0]], np.r_[values, values[0]])
    ax.fill(np.r_[angles, angles[0]], np.r_[values, values[0]], alpha=0.2)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels)
    ax.set_title("Behavior Radar")
    return _save(fig, path)


def plot_sankey_transition_diagram(state_report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Sankey Transition Diagram", state_report)
    graph = state_report.get("transition_graph", [])
    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    for row, edge in enumerate(graph):
        ax.plot([0, 1], [row, row], linewidth=max(1, edge["count"]), alpha=0.6)
        ax.text(-0.02, row, edge["from_state"], ha="right", va="center")
        ax.text(1.02, row, edge["to_state"], ha="left", va="center")
    ax.set_axis_off()
    ax.set_title("Transition Flow")
    return _save(fig, path)


def plot_behavioral_network_graph(state_report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Behavioral Network Graph", state_report)
    states = state_report.get("states", [])
    graph = state_report.get("transition_graph", [])
    angles = np.linspace(0, 2 * np.pi, len(states), endpoint=False) if states else np.array([])
    coords = {state: (np.cos(angle), np.sin(angle)) for state, angle in zip(states, angles)}
    fig, ax = plt.subplots(figsize=(5, 5), constrained_layout=True)
    for edge in graph:
        x0, y0 = coords[edge["from_state"]]
        x1, y1 = coords[edge["to_state"]]
        ax.plot([x0, x1], [y0, y1], alpha=0.3 + 0.05 * edge["count"])
    for state, (x, y) in coords.items():
        ax.scatter([x], [y], s=80)
        ax.text(x, y, state)
    ax.set_axis_off()
    ax.set_title("Behavioral Network")
    return _save(fig, path)


def plot_trajectory_clusters(similarity_report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Trajectory Clusters", similarity_report)
    matrix = np.asarray(similarity_report["metrics"]["trajectory_similarity"]["values"], dtype=float)
    labels = similarity_report["conditions"]
    coords = _embedding_from_similarity(matrix)
    fig, ax = plt.subplots(figsize=(5, 4), constrained_layout=True)
    ax.scatter(coords[:, 0], coords[:, 1])
    for label, (x, y) in zip(labels, coords):
        ax.text(x, y, label)
    ax.set_title("Trajectory Clusters")
    return _save(fig, path)


def plot_progression_map(intervention_report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Progression Map", intervention_report)
    rows = intervention_report.get("replay", [])
    fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
    for key in sorted({k for row in rows for k in row.get("parameters", {}) if isinstance(row["parameters"][k], (int, float))}):
        ax.plot([row["time_s"] for row in rows], [row["parameters"][key] for row in rows], marker="o", label=key)
    ax.set_xlabel("time (s)")
    ax.set_title("Computational Progression Map")
    if rows:
        ax.legend(loc="best")
    return _save(fig, path)


def plot_similarity_heatmap(similarity_report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Similarity Heatmap", similarity_report)
    matrix = np.asarray(similarity_report["behavioral_similarity_matrix"]["values"], dtype=float)
    labels = similarity_report["conditions"]
    fig, ax = plt.subplots(figsize=(5, 4), constrained_layout=True)
    image = ax.imshow(matrix, vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30)
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_title("Behavior Similarity")
    fig.colorbar(image, ax=ax)
    return _save(fig, path)


def plot_behavioral_embeddings(similarity_report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Behavioral Embeddings", similarity_report)
    matrix = np.asarray(similarity_report["behavioral_similarity_matrix"]["values"], dtype=float)
    labels = similarity_report["conditions"]
    coords = _embedding_from_similarity(matrix)
    fig, ax = plt.subplots(figsize=(5, 4), constrained_layout=True)
    ax.scatter(coords[:, 0], coords[:, 1])
    for label, (x, y) in zip(labels, coords):
        ax.text(x, y, label)
    ax.set_title("Behavioral Embedding")
    return _save(fig, path)


def export_replay_dashboard(report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = _path(output_path)
    if path.suffix == ".html":
        return _write_html(path, "Replay Dashboard", report)
    return plot_similarity_heatmap(report, path)


def _radar_metrics(report: Mapping[str, Any]) -> dict[str, float]:
    metrics = report.get("metrics", {})
    return {
        key.replace("_similarity", ""): float(np.mean(value["values"]))
        for key, value in metrics.items()
        if key.endswith("_similarity")
    }


def _embedding_from_similarity(matrix: np.ndarray) -> np.ndarray:
    if matrix.size == 0:
        return np.zeros((0, 2), dtype=float)
    centered = matrix - np.mean(matrix, axis=0)
    _, _, vh = np.linalg.svd(centered, full_matrices=False)
    coords = centered @ vh[: min(2, vh.shape[0])].T
    if coords.shape[1] == 1:
        coords = np.column_stack([coords[:, 0], np.zeros(coords.shape[0])])
    return coords[:, :2]


def _formats(formats: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(fmt.lower() for fmt in formats)
    unsupported = sorted(set(normalized) - set(VISUAL_EXPORT_FORMATS))
    if unsupported:
        raise ValueError(f"unsupported advanced visualization formats: {unsupported}")
    if not normalized:
        raise ValueError("at least one visualization format is required.")
    return normalized


def _path(output_path: str | Path) -> Path:
    path = Path(output_path)
    if path.suffix.lower() not in {".png", ".svg", ".pdf", ".html"}:
        raise ValueError("advanced visualization output must end in .png, .svg, .pdf, or .html.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _save(fig: plt.Figure, path: Path) -> Path:
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def _write_html(path: Path, title: str, payload: Mapping[str, Any]) -> Path:
    path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<title>{title}</title></head><body><h1>{title}</h1>"
        "<p>Computational visualization only; no biological validation claim.</p>"
        f"<pre>{payload}</pre></body></html>",
        encoding="utf-8",
    )
    return path


__all__ = [
    "VISUAL_EXPORT_FORMATS",
    "export_advanced_visualization_set",
    "export_replay_dashboard",
    "plot_behavioral_embeddings",
    "plot_behavioral_network_graph",
    "plot_behavioral_state_timeline",
    "plot_intervention_timeline",
    "plot_progression_map",
    "plot_radar_plot",
    "plot_sankey_transition_diagram",
    "plot_similarity_heatmap",
    "plot_trajectory_clusters",
]
