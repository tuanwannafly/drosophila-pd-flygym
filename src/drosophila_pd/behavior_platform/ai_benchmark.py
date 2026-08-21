"""Benchmark suite for v2 behavioral datasets and analysis outputs."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    role: str
    metrics: Mapping[str, float]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "role": self.role,
            "metrics": dict(self.metrics),
            "metadata": dict(self.metadata),
        }


def run_behavior_benchmark(cases: Sequence[BenchmarkCase]) -> dict[str, Any]:
    """Generate leaderboard, comparison table, and benchmark report."""

    if not cases:
        raise ValueError("benchmark requires at least one case.")
    metric_names = sorted({name for case in cases for name in case.metrics})
    rows = []
    for case in cases:
        score = float(np.mean([case.metrics.get(metric, 0.0) for metric in metric_names])) if metric_names else 0.0
        rows.append({"case_id": case.case_id, "role": case.role, "score": score, **case.metrics})
    leaderboard = sorted(rows, key=lambda row: row["score"], reverse=True)
    baseline = leaderboard[0]
    comparison = [
        {
            "case_id": row["case_id"],
            "role": row["role"],
            **{f"delta_{metric}": row.get(metric, 0.0) - baseline.get(metric, 0.0) for metric in metric_names},
        }
        for row in rows
    ]
    return {
        "benchmark_version": 2,
        "scientific_scope": "Computational benchmark only; no biological validation claim.",
        "roles": sorted({case.role for case in cases}),
        "metric_names": metric_names,
        "leaderboard": leaderboard,
        "comparison_table": comparison,
        "benchmark_report": {
            "case_count": len(cases),
            "top_case_id": leaderboard[0]["case_id"],
            "custom_dataset_supported": True,
        },
    }


def export_benchmark_report(report: Mapping[str, Any], output_dir: str | Path) -> dict[str, Path]:
    """Export benchmark report JSON and CSV tables."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    files = {
        "json": output / "benchmark_report.json",
        "leaderboard_csv": output / "leaderboard.csv",
        "comparison_csv": output / "comparison_table.csv",
    }
    files["json"].write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    _write_rows(files["leaderboard_csv"], report["leaderboard"])
    _write_rows(files["comparison_csv"], report["comparison_table"])
    return files


def _write_rows(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


__all__ = ["BenchmarkCase", "export_benchmark_report", "run_behavior_benchmark"]
