"""Optional matplotlib visualizations for computational reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from .model import COMPUTATIONAL_SCOPE


def render_pd_figures(
    report: Mapping[str, Any],
    output_dir: str | Path,
    *,
    formats: Sequence[str] = ("png", "svg"),
) -> dict[str, list[str]]:
    """Render available report arrays without inventing missing observations."""

    paths: dict[str, list[str]] = {}
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    jobs = {
        "motor_feature_timelines": plot_motor_feature_timelines,
        "behavior_timeline": plot_behavior_timeline,
        "feature_importance": plot_feature_importance,
        "index_breakdown": plot_index_breakdown,
        "correlation_heatmap": plot_correlation_heatmap,
        "radar": plot_radar,
        "parallel_coordinates": plot_parallel_coordinates,
        "distributions": plot_distributions,
    }
    for name, function in jobs.items():
        figure = function(report)
        if figure is None:
            continue
        figure_paths = []
        for extension in formats:
            path = output / f"{name}.{extension.lstrip('.') }"
            figure.savefig(path, dpi=160, bbox_inches="tight")
            figure_paths.append(str(path))
        figure.clf()
        _close(figure)
        paths[name] = figure_paths
    return paths


def plot_motor_feature_timelines(report):
    values = report.get("motor_features", {}).get("sample_values", {})
    return _line_figure(values, "Motor feature samples", "sample", "value")


def plot_behavior_timeline(report):
    timeline = report.get("behavior_model", {}).get("summary", {}).get("timeline", [])
    if not timeline:
        return None
    plt, figure, axis = _figure("Behavior state timeline")
    times = [row["time_s"] for row in timeline]
    labels = [row["state"] for row in timeline]
    unique = {label: index for index, label in enumerate(sorted(set(labels)))}
    axis.step(times, [unique[label] for label in labels], where="post")
    axis.set_yticks(list(unique.values()), list(unique.keys()))
    axis.set_xlabel("Time (s)")
    axis.set_ylabel("Computational state")
    return figure


def plot_feature_importance(report):
    components = report.get("computational_pd_index", {}).get("feature_importance", {})
    return _bar_figure(components, "Configured feature contribution", "feature", "relative contribution")


def plot_index_breakdown(report):
    components = report.get("computational_pd_index", {}).get("components", {})
    values = {name: item.get("score") for name, item in components.items() if item.get("available")}
    return _bar_figure(values, "Computational index component scores", "feature", "relative deviation")


def plot_correlation_heatmap(report):
    correlation = report.get("validation", {}).get("correlation", {})
    values = correlation.get("values")
    names = correlation.get("features", [])
    if not values:
        return None
    plt, figure, axis = _figure("Feature correlation")
    image = axis.imshow(values, vmin=-1, vmax=1, cmap="coolwarm")
    axis.set_xticks(range(len(names)), names, rotation=90)
    axis.set_yticks(range(len(names)), names)
    figure.colorbar(image, ax=axis)
    return figure


def plot_radar(report):
    values = report.get("motor_features", {}).get("values", {})
    finite = {name: value for name, value in values.items() if value is not None}
    if not finite:
        return None
    plt, figure, axis = _figure("Available motor features")
    names = list(finite)
    axis.bar(range(len(names)), list(finite.values()))
    axis.set_xticks(range(len(names)), names, rotation=90)
    axis.set_ylabel("observed value")
    return figure


def plot_parallel_coordinates(report):
    values = report.get("motor_features", {}).get("values", {})
    finite = {name: value for name, value in values.items() if value is not None}
    return _line_figure({"observed": list(finite.values())}, "Feature profile", "feature index", "value") if finite else None


def plot_distributions(report):
    values = report.get("motor_features", {}).get("sample_values", {})
    return _hist_figure(values, "Motor feature distributions")


def _line_figure(series: Mapping[str, Sequence[float]], title: str, xlabel: str, ylabel: str):
    finite = {name: list(values) for name, values in series.items() if values}
    if not finite:
        return None
    plt, figure, axis = _figure(title)
    for name, values in finite.items():
        axis.plot(range(len(values)), values, label=name)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    if len(finite) <= 8:
        axis.legend()
    return figure


def _bar_figure(values: Mapping[str, Any], title: str, xlabel: str, ylabel: str):
    finite = {name: float(value) for name, value in values.items() if _number(value)}
    if not finite:
        return None
    plt, figure, axis = _figure(title)
    axis.bar(range(len(finite)), list(finite.values()))
    axis.set_xticks(range(len(finite)), list(finite), rotation=90)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    return figure


def _hist_figure(series: Mapping[str, Sequence[float]], title: str):
    finite = {name: values for name, values in series.items() if values}
    if not finite:
        return None
    plt, figure, axis = _figure(title)
    for name, values in finite.items():
        axis.hist(values, bins=min(20, max(1, len(values))), alpha=0.45, label=name)
    axis.set_xlabel("value")
    axis.set_ylabel("count")
    if len(finite) <= 8:
        axis.legend()
    return figure


def _figure(title: str):
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(9, 5))
    axis.set_title(title)
    figure.text(0.01, 0.01, COMPUTATIONAL_SCOPE, fontsize=6)
    return plt, figure, axis


def _number(value: Any) -> bool:
    try:
        return bool(value is not None and __import__("math").isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _close(figure) -> None:
    import matplotlib.pyplot as plt

    plt.close(figure)


__all__ = [
    "plot_behavior_timeline",
    "plot_correlation_heatmap",
    "plot_distributions",
    "plot_feature_importance",
    "plot_index_breakdown",
    "plot_motor_feature_timelines",
    "plot_parallel_coordinates",
    "plot_radar",
    "render_pd_figures",
]
