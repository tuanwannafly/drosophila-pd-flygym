"""Validation plots generated from observed/reference arrays only."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData


def render_validation_figures(
    observed: RolloutData,
    reference: RolloutData,
    output_dir: str | Path,
    *,
    formats: Sequence[str] = ("png", "svg"),
) -> dict[str, list[str]]:
    """Render requested agreement plots for two imported rollouts."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    jobs = {
        "trajectory_overlay": _trajectory_overlay,
        "joint_overlay": _joint_overlay,
        "com_overlay": _com_overlay,
        "difference_heatmap": _difference_heatmap,
        "residual_plots": _residual_plot,
        "prediction_vs_reference": _prediction_plot,
        "correlation_plots": _correlation_plot,
        "agreement_plots": _agreement_plot,
        "error_histograms": _error_histogram,
    }
    paths: dict[str, list[str]] = {}
    for name, builder in jobs.items():
        figure = builder(observed, reference)
        if figure is None:
            continue
        saved = []
        for extension in formats:
            path = output / f"{name}.{extension.lstrip('.') }"
            figure.savefig(path, dpi=160, bbox_inches="tight")
            saved.append(str(path))
        paths[name] = saved
        _close(figure)
    return paths


def _trajectory_overlay(observed, reference):
    plt, figure, axis = _figure("Trajectory overlay")
    for rollout, label in ((reference, "reference"), (observed, "observed")):
        positions = rollout.positions_array()
        axis.plot(positions[:, 0], positions[:, 1], label=label)
    axis.set_xlabel("x (mm)")
    axis.set_ylabel("y (mm)")
    axis.legend()
    return figure


def _joint_overlay(observed, reference):
    common = sorted(set(observed.joint_arrays()) & set(reference.joint_arrays()))
    if not common:
        return None
    joint = common[0]
    plt, figure, axis = _figure(f"Joint overlay: {joint}")
    axis.plot(reference.joint_arrays()[joint].ravel(), label="reference")
    axis.plot(observed.joint_arrays()[joint].ravel(), label="observed")
    axis.set_xlabel("sample")
    axis.set_ylabel("joint value")
    axis.legend()
    return figure


def _com_overlay(observed, reference):
    left = observed.com_array()
    right = reference.com_array()
    if left is None or right is None:
        return None
    plt, figure, axis = _figure("COM overlay")
    axis.plot(right[:, 0], right[:, 1], label="reference")
    axis.plot(left[:, 0], left[:, 1], label="observed")
    axis.set_xlabel("x (mm)")
    axis.set_ylabel("y (mm)")
    axis.legend()
    return figure


def _difference_heatmap(observed, reference):
    left = observed.positions_array()
    right = reference.positions_array()
    if left.shape != right.shape:
        return None
    plt, figure, axis = _figure("Trajectory difference heatmap")
    image = axis.imshow(np.abs(left - right).T, aspect="auto", interpolation="nearest")
    axis.set_xlabel("coordinate sample")
    axis.set_ylabel("coordinate")
    figure.colorbar(image, ax=axis, label="absolute error")
    return figure


def _residual_plot(observed, reference):
    left, right = _paired_positions(observed, reference)
    if left is None:
        return None
    plt, figure, axis = _figure("Residual plot")
    residual = left - right
    axis.plot(residual)
    axis.axhline(0.0, color="black", linewidth=0.8)
    axis.set_xlabel("flattened sample")
    axis.set_ylabel("observed - reference")
    return figure


def _prediction_plot(observed, reference):
    left, right = _paired_positions(observed, reference)
    if left is None:
        return None
    plt, figure, axis = _figure("Observed versus reference")
    axis.scatter(right, left, s=8)
    axis.set_xlabel("reference")
    axis.set_ylabel("observed")
    return figure


def _correlation_plot(observed, reference):
    left, right = _paired_positions(observed, reference)
    if left is None:
        return None
    correlation = float(np.corrcoef(left, right)[0, 1]) if np.std(left) > 1e-12 and np.std(right) > 1e-12 else 0.0
    plt, figure, axis = _figure(f"Correlation (r={correlation:.4f})")
    axis.plot(left, label="observed")
    axis.plot(right, label="reference")
    axis.legend()
    return figure


def _agreement_plot(observed, reference):
    left, right = _paired_positions(observed, reference)
    if left is None:
        return None
    plt, figure, axis = _figure("Agreement plot")
    mean = (left + right) / 2.0
    difference = left - right
    axis.scatter(mean, difference, s=8)
    axis.axhline(0.0, color="black", linewidth=0.8)
    axis.set_xlabel("mean of observed/reference")
    axis.set_ylabel("difference")
    return figure


def _error_histogram(observed, reference):
    left, right = _paired_positions(observed, reference)
    if left is None:
        return None
    plt, figure, axis = _figure("Absolute error histogram")
    axis.hist(np.abs(left - right), bins=min(30, max(1, left.size)), alpha=0.8)
    axis.set_xlabel("absolute error")
    axis.set_ylabel("count")
    return figure


def _paired_positions(observed, reference):
    left = observed.positions_array().ravel()
    right = reference.positions_array().ravel()
    return (left, right) if left.shape == right.shape else (None, None)


def _figure(title):
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.set_title(title)
    figure.text(0.01, 0.01, "Observed/reference computational agreement only; not biological validation.", fontsize=6)
    return plt, figure, axis


def _close(figure):
    import matplotlib.pyplot as plt

    plt.close(figure)


__all__ = ["render_validation_figures"]
