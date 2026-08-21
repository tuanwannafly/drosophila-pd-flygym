"""Scenario management for v2 digital twin workflows."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    role: str
    parameters: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "role": self.role,
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ScenarioResult:
    scenario_id: str
    role: str
    report: Mapping[str, Any]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "role": self.role,
            "report": dict(self.report),
            "metadata": dict(self.metadata),
        }


def build_scenario(
    scenario_id: str,
    *,
    role: str,
    parameters: Mapping[str, Any],
    metadata: Mapping[str, Any] | None = None,
) -> ScenarioDefinition:
    """Create a computational scenario definition."""

    return ScenarioDefinition(
        scenario_id=scenario_id,
        role=role,
        parameters=dict(parameters),
        metadata=dict(metadata or {}),
    )


def batch_execute_scenarios(
    scenarios: Sequence[ScenarioDefinition],
    executor: Callable[[ScenarioDefinition], Mapping[str, Any]],
) -> list[ScenarioResult]:
    """Execute scenario definitions through a caller-provided pure function."""

    return [
        ScenarioResult(
            scenario_id=scenario.scenario_id,
            role=scenario.role,
            report=dict(executor(scenario)),
            metadata={"execution_order": index},
        )
        for index, scenario in enumerate(scenarios)
    ]


def compare_scenarios(results: Sequence[ScenarioResult]) -> dict[str, Any]:
    """Create a JSON-ready scenario comparison report."""

    if len(results) < 2:
        raise ValueError("at least two scenario results are required.")
    metric_names = sorted(
        {
            name
            for result in results
            for name, value in result.report.items()
            if _is_number(value)
        }
    )
    baseline = results[0]
    deltas = {
        result.scenario_id: {
            metric: _delta(result.report.get(metric), baseline.report.get(metric))
            for metric in metric_names
        }
        for result in results[1:]
    }
    return {
        "scenario_comparison_version": 2,
        "scientific_scope": (
            "Scenario comparison uses computational reports only and does not "
            "run simulations or create biological claims."
        ),
        "baseline_scenario": baseline.scenario_id,
        "scenarios": [result.as_dict() for result in results],
        "metric_names": metric_names,
        "deltas_from_baseline": deltas,
    }


def scenario_report_to_json(report: Mapping[str, Any], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _delta(value: Any, baseline: Any) -> float | None:
    if not _is_number(value) or not _is_number(baseline):
        return None
    return float(value) - float(baseline)


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


__all__ = [
    "ScenarioDefinition",
    "ScenarioResult",
    "batch_execute_scenarios",
    "build_scenario",
    "compare_scenarios",
    "scenario_report_to_json",
]
