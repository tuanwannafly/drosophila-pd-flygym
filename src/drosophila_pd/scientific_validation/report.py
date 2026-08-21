"""Scientific validation report and publication-asset generation."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.rollout import RolloutData

from .datasets import ReferenceDatasetManager
from .metrics import compare_rollouts
from .reproducibility import hash_payload
from .statistics import validate_statistical_stability
from .visualization import render_validation_figures


def generate_validation_report(
    observed: RolloutData,
    reference: RolloutData,
    *,
    output_dir: str | Path | None = None,
    manager: ReferenceDatasetManager | None = None,
    manager_base_dir: str | Path | None = None,
    observed_features: Mapping[str, Any] | None = None,
    reference_features: Mapping[str, Any] | None = None,
    observed_analysis: Mapping[str, Any] | None = None,
    reference_analysis: Mapping[str, Any] | None = None,
    statistical_samples: Mapping[str, Sequence[float]] | None = None,
    benchmark_report: Mapping[str, Any] | None = None,
    reproducibility_report: Mapping[str, Any] | None = None,
    write_figures: bool = True,
) -> dict[str, Any]:
    """Build validation artifacts from one observed/reference pair."""

    comparison = compare_rollouts(
        observed,
        reference,
        observed_features=observed_features,
        reference_features=reference_features,
        observed_analysis=observed_analysis,
        reference_analysis=reference_analysis,
    )
    report: dict[str, Any] = {
        "scientific_validation_version": 1,
        "overall_pass": _comparison_pass(comparison),
        "scope": "Computational agreement and software reproducibility over supplied rollout/reference data only; not biological validation.",
        "observed": observed.as_metadata(),
        "reference": reference.as_metadata(),
        "comparison": comparison,
        "dataset_summary": manager.manifest(base_dir=manager_base_dir) if manager is not None else {"available": False, "reason": "No reference dataset manager supplied."},
        "statistical_validation": validate_statistical_stability(statistical_samples) if statistical_samples else {"available": False, "reason": "No statistical sample arrays supplied."},
        "benchmark": dict(benchmark_report or {"available": False, "reason": "No benchmark operation supplied."}),
        "reproducibility": dict(reproducibility_report or {"available": False, "reason": "No repeated operation supplied."}),
    }
    report["report_sha256"] = hash_payload(report)
    if output_dir is not None:
        _write_package(
            report,
            observed,
            reference,
            Path(output_dir),
            write_figures=write_figures,
        )
    return report


def _write_package(report, observed, reference, output: Path, *, write_figures: bool) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = _json_safe(report)
    (output / "validation_report.json").write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    (output / "benchmark_report.json").write_text(json.dumps(payload["benchmark"], indent=2, sort_keys=True), encoding="utf-8")
    (output / "reproducibility_report.json").write_text(json.dumps(payload["reproducibility"], indent=2, sort_keys=True), encoding="utf-8")
    (output / "dataset_summary.json").write_text(json.dumps(payload["dataset_summary"], indent=2, sort_keys=True), encoding="utf-8")
    markdown = render_validation_markdown(payload)
    (output / "validation_report.md").write_text(markdown, encoding="utf-8")
    (output / "validation_report.html").write_text("<html><body><pre>" + html.escape(markdown) + "</pre></body></html>", encoding="utf-8")
    _write_validation_table(payload, output / "validation_summary.csv")
    _write_index(payload, output / "table_index.csv", ["validation_summary.csv"])
    (output / "method_summary.md").write_text(_method_summary(), encoding="utf-8")
    (output / "supplementary_appendix.md").write_text(_supplementary_appendix(payload), encoding="utf-8")
    figure_paths = render_validation_figures(observed, reference, output / "figures") if write_figures else {}
    (output / "figure_manifest.json").write_text(json.dumps(_json_safe(figure_paths), indent=2, sort_keys=True), encoding="utf-8")
    _write_index(payload, output / "figure_index.csv", sorted({path for paths in figure_paths.values() for path in paths}))


def render_validation_markdown(report: Mapping[str, Any]) -> str:
    comparison = report.get("comparison", {})
    lines = [
        "# Scientific Validation Report",
        "",
        f"- Overall software agreement pass: `{report.get('overall_pass', False)}`",
        f"- Observed condition: `{report.get('observed', {}).get('condition_id', 'unknown')}`",
        f"- Reference condition: `{report.get('reference', {}).get('condition_id', 'unknown')}`",
        "",
        "## Scope",
        "",
        report.get("scope", ""),
        "",
        "## Field comparison",
        "",
        "| Field | Available | RMSE | MAE | R² | Correlation |",
        "|---|:---:|---:|---:|---:|---:|",
    ]
    for name, result in comparison.get("fields", {}).items():
        lines.append(f"| `{name}` | {result.get('available', False)} | {result.get('rmse', 'N/A')} | {result.get('mae', 'N/A')} | {result.get('r2', 'N/A')} | {result.get('correlation', 'N/A')} |")
    lines.extend(["", "## Scientific boundary", "", "The report describes computational agreement against supplied data. It does not establish biological validity or clinical meaning.", ""])
    return "\n".join(lines)


def _comparison_pass(comparison: Mapping[str, Any]) -> bool:
    fields = comparison.get("fields", {})
    required = ("trajectory", "orientation")
    return bool(fields) and all(fields.get(name, {}).get("available", False) for name in required)


def _write_validation_table(report, path: Path) -> None:
    rows = []
    for name, result in report.get("comparison", {}).get("fields", {}).items():
        if "rmse" in result:
            rows.append({"field": name, "available": result.get("available"), "rmse": result.get("rmse"), "mae": result.get("mae"), "relative_error": result.get("relative_error_mean"), "r2": result.get("r2"), "correlation": result.get("correlation")})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["field", "available", "rmse", "mae", "relative_error", "r2", "correlation"])
        writer.writeheader()
        writer.writerows(rows)


def _write_index(report, path: Path, values) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["identifier", "path", "evidence_dependency"])
        writer.writeheader()
        for index, value in enumerate(values):
            writer.writerow({"identifier": f"asset_{index:03d}", "path": value, "evidence_dependency": "supplied observed/reference arrays"})


def _method_summary() -> str:
    return """# Method Summary\n\nThis package compares imported observed and reference arrays directly. It reports absolute error, relative error, RMSE, MAE, R² and correlation when shapes and finite values permit. Missing arrays remain unavailable. No simulation or synthetic rollout is created.\n"""


def _supplementary_appendix(report) -> str:
    return """# Supplementary Appendix\n\nThe machine-readable `validation_report.json`, `validation_summary.csv`, figure manifest and reproducibility/benchmark reports are generated from the supplied input pair. Their computational scope does not imply biological or clinical validation.\n\n## Report hash\n\n`{}`\n""".format(report.get("report_sha256", "unavailable"))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return _json_safe(value.item())
    return value


__all__ = ["generate_validation_report", "render_validation_markdown"]
