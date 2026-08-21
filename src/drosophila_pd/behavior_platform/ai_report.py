"""Automatic report generation for v2 AI behavioral analysis."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


REPORT_FORMATS = ("markdown", "html", "pdf", "json", "csv")


def generate_ai_behavior_report(
    *,
    dataset_summary: Mapping[str, Any],
    feature_summary: Mapping[str, Any],
    analysis_summary: Mapping[str, Any],
    benchmark_summary: Mapping[str, Any],
    output_dir: str | Path,
    formats: Sequence[str] = REPORT_FORMATS,
) -> dict[str, Path]:
    """Generate Markdown, HTML, PDF, JSON, and CSV reports."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    normalized = tuple(fmt.lower() for fmt in formats)
    unsupported = sorted(set(normalized) - set(REPORT_FORMATS))
    if unsupported:
        raise ValueError(f"unsupported report formats: {unsupported}")
    if not normalized:
        raise ValueError("at least one report format is required.")
    payload = {
        "report_version": 2,
        "scientific_scope": "AI-assisted computational report only; no biological validation claim.",
        "dataset_summary": dict(dataset_summary),
        "feature_summary": dict(feature_summary),
        "analysis_summary": dict(analysis_summary),
        "benchmark_summary": dict(benchmark_summary),
    }
    plot_path = _write_plot(payload, output / "behavior_summary.png")
    payload["plots"] = {"behavior_summary_png": str(plot_path)}
    files: dict[str, Path] = {"plot_png": plot_path}
    if "json" in normalized:
        files["json"] = output / "ai_behavior_report.json"
        files["json"].write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if "markdown" in normalized:
        files["markdown"] = output / "ai_behavior_report.md"
        files["markdown"].write_text(_markdown(payload), encoding="utf-8")
    if "html" in normalized:
        files["html"] = output / "ai_behavior_report.html"
        files["html"].write_text(_html(payload), encoding="utf-8")
    if "pdf" in normalized:
        files["pdf"] = output / "ai_behavior_report.pdf"
        _write_pdf(payload, files["pdf"])
    if "csv" in normalized:
        files["csv"] = output / "ai_behavior_summary.csv"
        _write_csv(payload, files["csv"])
    return files


def _write_plot(payload: Mapping[str, Any], path: Path) -> Path:
    labels = ["samples", "features", "benchmarks"]
    values = [
        payload["dataset_summary"].get("sample_count", 0),
        len(payload["feature_summary"].get("feature_names", ())),
        payload["benchmark_summary"].get("benchmark_report", {}).get("case_count", 0),
    ]
    fig, ax = plt.subplots(figsize=(5, 3), constrained_layout=True)
    ax.bar(labels, values)
    ax.set_title("AI Behavior Report Summary")
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def _markdown(payload: Mapping[str, Any]) -> str:
    return (
        "# AI Behavioral Analysis Report\n\n"
        f"{payload['scientific_scope']}\n\n"
        f"- Dataset samples: {payload['dataset_summary'].get('sample_count', 0)}\n"
        f"- Feature count: {len(payload['feature_summary'].get('feature_names', ())) }\n"
        f"- Benchmark cases: {payload['benchmark_summary'].get('benchmark_report', {}).get('case_count', 0)}\n"
    )


def _html(payload: Mapping[str, Any]) -> str:
    return (
        "<!doctype html><html><head><meta charset='utf-8'><title>AI Behavioral Analysis</title></head>"
        "<body><h1>AI Behavioral Analysis Report</h1>"
        f"<p>{payload['scientific_scope']}</p>"
        f"<pre>{json.dumps(payload, indent=2, sort_keys=True)}</pre></body></html>"
    )


def _write_pdf(payload: Mapping[str, Any], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5), constrained_layout=True)
    ax.axis("off")
    ax.text(0.02, 0.9, "AI Behavioral Analysis Report", fontsize=16)
    ax.text(0.02, 0.78, payload["scientific_scope"], wrap=True)
    ax.text(0.02, 0.6, f"Samples: {payload['dataset_summary'].get('sample_count', 0)}")
    ax.text(0.02, 0.5, f"Features: {len(payload['feature_summary'].get('feature_names', ())) }")
    fig.savefig(path)
    plt.close(fig)


def _write_csv(payload: Mapping[str, Any], path: Path) -> None:
    rows = [
        {"section": "dataset", "metric": "sample_count", "value": payload["dataset_summary"].get("sample_count", 0)},
        {"section": "features", "metric": "feature_count", "value": len(payload["feature_summary"].get("feature_names", ()))},
        {
            "section": "benchmark",
            "metric": "case_count",
            "value": payload["benchmark_summary"].get("benchmark_report", {}).get("case_count", 0),
        },
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["section", "metric", "value"])
        writer.writeheader()
        writer.writerows(rows)


__all__ = ["REPORT_FORMATS", "generate_ai_behavior_report"]
