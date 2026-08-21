"""Machine-readable and human-readable computational phenotype reports."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.rollout import RolloutData

from .model import COMPUTATIONAL_SCOPE, ComputationalPDIndex, ParkinsonMotorConfig, ParkinsonMotorModel
from .validation import (
    correlation_matrix,
    cross_validate_index,
    leave_one_out_feature_validation,
    outlier_sensitivity,
    validate_computational_report,
)
from .visualization import render_pd_figures


def generate_computational_pd_report(
    rollout: RolloutData,
    *,
    output_dir: str | Path | None = None,
    config: ParkinsonMotorConfig | Mapping[str, Any] | None = None,
    reference_features: Mapping[str, float | None] | None = None,
    feature_rows: Sequence[Mapping[str, float | None]] | None = None,
    write_figures: bool = True,
) -> dict[str, Any]:
    """Analyze an imported rollout and optionally write a report package."""

    model = ParkinsonMotorModel(config)
    report = (
        model.evaluate_against_reference(rollout, reference_features)
        if reference_features is not None
        else model.evaluate(rollout)
    )
    samples = report["motor_features"]["sample_values"]
    report["validation"] = {
        "correlation": correlation_matrix(samples),
        "outlier_sensitivity": {name: outlier_sensitivity(values) for name, values in samples.items()},
    }
    if reference_features is not None and feature_rows:
        index = ComputationalPDIndex(
            weights=model.config.index_weights,
            directions=model.config.index_directions,
        )
        report["validation"]["cross_validation"] = cross_validate_index(
            index, feature_rows, reference_features
        )
        report["validation"]["leave_one_out"] = leave_one_out_feature_validation(
            index, feature_rows, reference_features
        )
    else:
        unavailable = {"available": False, "reason": "Independent feature rows were not supplied."}
        report["validation"]["cross_validation"] = unavailable
        report["validation"]["leave_one_out"] = unavailable
    report["validation"]["report_checks"] = validate_computational_report(report)
    report["scope"] = COMPUTATIONAL_SCOPE
    if output_dir is not None:
        _write_report_package(report, Path(output_dir), write_figures=write_figures)
    return report


def _write_report_package(report: Mapping[str, Any], output: Path, *, write_figures: bool) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = _json_safe(report)
    (output / "computational_pd_report.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    _write_feature_csv(payload, output / "motor_features.csv")
    markdown = render_markdown_report(payload)
    (output / "computational_pd_report.md").write_text(markdown, encoding="utf-8")
    (output / "computational_pd_report.html").write_text(
        "<html><body><pre>" + html.escape(markdown) + "</pre></body></html>",
        encoding="utf-8",
    )
    if write_figures:
        render_pd_figures(payload, output / "figures")


def render_markdown_report(report: Mapping[str, Any]) -> str:
    """Render a concise report without changing the underlying observations."""

    rollout = report.get("rollout", {})
    validation = report.get("validation", {}).get("report_checks", {})
    lines = [
        "# Computational Parkinson Phenotype Report",
        "",
        f"- Condition: `{rollout.get('condition_id', 'unknown')}`",
        f"- Samples: `{rollout.get('sample_count', 'unknown')}`",
        f"- Timestep (s): `{rollout.get('timestep_s', 'unknown')}`",
        f"- Validation pass: `{validation.get('overall_pass', False)}`",
        "",
        "## Scientific scope",
        "",
        COMPUTATIONAL_SCOPE,
        "",
        "## Motor features",
        "",
        "| Feature | Value | Available |",
        "|---|---:|:---:|",
    ]
    values = report.get("motor_features", {}).get("values", {})
    available = report.get("motor_features", {}).get("available", {})
    for name, value in values.items():
        lines.append(f"| `{name}` | {value if value is not None else 'N/A'} | {available.get(name, False)} |")
    lines.extend(["", "## Behavior model", "", "Computational state labels and transitions are derived from supplied rollout arrays.", ""])
    return "\n".join(lines)


def _write_feature_csv(report: Mapping[str, Any], path: Path) -> None:
    values = report.get("motor_features", {}).get("values", {})
    available = report.get("motor_features", {}).get("available", {})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["feature", "value", "available"])
        writer.writeheader()
        for name, value in values.items():
            writer.writerow({"feature": name, "value": value, "available": available.get(name, False)})


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


__all__ = ["generate_computational_pd_report", "render_markdown_report"]
