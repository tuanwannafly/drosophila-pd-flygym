"""Interactive analytics specifications for v2 AI behavior workflows."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


ANALYTICS_PANELS = (
    "interactive_dashboard",
    "behavior_explorer",
    "cluster_explorer",
    "embedding_explorer",
    "timeline_explorer",
    "dataset_explorer",
    "comparison_explorer",
)


def build_ai_analytics_dashboard(
    *,
    dataset_summary: Mapping[str, Any],
    embedding_report: Mapping[str, Any],
    clustering_report: Mapping[str, Any],
    comparison_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a portable interactive analytics specification."""

    return {
        "ai_analytics_version": 2,
        "scientific_scope": "Interactive computational analytics only; no biological validation claim.",
        "panels": list(ANALYTICS_PANELS),
        "filters": {
            "condition_selector": True,
            "sample_selector": True,
            "cluster_selector": True,
            "timeline_slider": True,
        },
        "dataset_summary": dict(dataset_summary),
        "embedding_report": dict(embedding_report),
        "clustering_report": dict(clustering_report),
        "comparison_report": dict(comparison_report or {}),
    }


def export_ai_analytics_dashboard(report: Mapping[str, Any], output_path: str | Path) -> Path:
    """Export an analytics dashboard as portable HTML."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>AI Behavior Analytics</title></head>"
        "<body><h1>AI Behavior Analytics</h1>"
        "<p>Computational analytics only; no biological validation claim.</p>"
        f"<pre>{json.dumps(report, indent=2, sort_keys=True)}</pre></body></html>",
        encoding="utf-8",
    )
    return path


def analytics_panel_inventory() -> list[str]:
    """Return supported interactive analytics panels."""

    return list(ANALYTICS_PANELS)


__all__ = [
    "ANALYTICS_PANELS",
    "analytics_panel_inventory",
    "build_ai_analytics_dashboard",
    "export_ai_analytics_dashboard",
]
