"""Generic computational intervention framework for v2 Session10."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence


INTERVENTION_SCOPE = (
    "Computational parameter modification only. Interventions in this module "
    "are not biological treatments, pharmacology, L-DOPA models, rescue "
    "experiments, or disease mechanisms."
)


@dataclass(frozen=True)
class ParameterSchedule:
    parameter: str
    times_s: tuple[float, ...]
    values: tuple[Any, ...]
    interpolation: str = "linear"

    def value_at(self, time_s: float) -> Any:
        if len(self.times_s) != len(self.values):
            raise ValueError("times_s and values lengths must match.")
        if not self.times_s:
            raise ValueError("parameter schedule requires at least one time.")
        value = float(time_s)
        if value <= self.times_s[0]:
            return self.values[0]
        if value >= self.times_s[-1]:
            return self.values[-1]
        for index in range(len(self.times_s) - 1):
            left_t = self.times_s[index]
            right_t = self.times_s[index + 1]
            if left_t <= value <= right_t:
                left = self.values[index]
                right = self.values[index + 1]
                if self.interpolation == "step" or not (_is_number(left) and _is_number(right)):
                    return left
                fraction = (value - left_t) / (right_t - left_t)
                return float(left) + fraction * (float(right) - float(left))
        return self.values[-1]

    def as_dict(self) -> dict[str, Any]:
        return {
            "parameter": self.parameter,
            "times_s": [float(value) for value in self.times_s],
            "values": list(self.values),
            "interpolation": self.interpolation,
        }


@dataclass(frozen=True)
class InterventionDefinition:
    intervention_id: str
    parameter_modifications: Mapping[str, Any]
    schedules: tuple[ParameterSchedule, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "intervention_id": self.intervention_id,
            "scientific_scope": INTERVENTION_SCOPE,
            "parameter_modifications": dict(self.parameter_modifications),
            "schedules": [schedule.as_dict() for schedule in self.schedules],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class StagedIntervention:
    stage_name: str
    start_time_s: float
    intervention: InterventionDefinition
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "stage_name": self.stage_name,
            "start_time_s": float(self.start_time_s),
            "intervention": self.intervention.as_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class InterventionTimeline:
    timeline_id: str
    stages: tuple[StagedIntervention, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "timeline_id": self.timeline_id,
            "scientific_scope": INTERVENTION_SCOPE,
            "stages": [stage.as_dict() for stage in self.stages],
            "metadata": dict(self.metadata),
        }


def intervention_from_config(config: Mapping[str, Any] | str | Path) -> InterventionTimeline:
    """Load a computational intervention timeline from mapping or JSON."""

    data = _load_config(config)
    stages = []
    for item in data.get("stages", ()):
        definition_data = item["intervention"]
        schedules = tuple(
            ParameterSchedule(
                parameter=str(schedule["parameter"]),
                times_s=tuple(float(value) for value in schedule.get("times_s", ())),
                values=tuple(schedule.get("values", ())),
                interpolation=str(schedule.get("interpolation", "linear")),
            )
            for schedule in definition_data.get("schedules", ())
        )
        definition = InterventionDefinition(
            intervention_id=str(definition_data["intervention_id"]),
            parameter_modifications=dict(definition_data.get("parameter_modifications", {})),
            schedules=schedules,
            metadata=dict(definition_data.get("metadata", {})),
        )
        stages.append(
            StagedIntervention(
                stage_name=str(item["stage_name"]),
                start_time_s=float(item["start_time_s"]),
                intervention=definition,
                metadata=dict(item.get("metadata", {})),
            )
        )
    timeline = InterventionTimeline(
        timeline_id=str(data.get("timeline_id", "computational_intervention")),
        stages=tuple(sorted(stages, key=lambda stage: stage.start_time_s)),
        metadata=dict(data.get("metadata", {})),
    )
    if not timeline.stages:
        raise ValueError("intervention timeline requires at least one stage.")
    return timeline


def apply_intervention_parameters(
    base_parameters: Mapping[str, Any],
    intervention: InterventionDefinition,
    *,
    time_s: float = 0.0,
) -> dict[str, Any]:
    """Apply one intervention definition to a parameter mapping."""

    result = dict(base_parameters)
    result.update(intervention.parameter_modifications)
    for schedule in intervention.schedules:
        result[schedule.parameter] = schedule.value_at(float(time_s))
    return result


def replay_intervention(
    timeline: InterventionTimeline,
    *,
    base_parameters: Mapping[str, Any],
    sample_times_s: Sequence[float],
) -> dict[str, Any]:
    """Replay intervention parameters at deterministic sample times."""

    rows = []
    for time_s in sample_times_s:
        stage = _stage_at(timeline, float(time_s))
        rows.append(
            {
                "time_s": float(time_s),
                "stage_name": stage.stage_name,
                "parameters": apply_intervention_parameters(
                    base_parameters,
                    stage.intervention,
                    time_s=float(time_s) - stage.start_time_s,
                ),
            }
        )
    return {
        "intervention_replay_version": 2,
        "scientific_scope": INTERVENTION_SCOPE,
        "timeline": timeline.as_dict(),
        "sample_times_s": [float(value) for value in sample_times_s],
        "replay": rows,
    }


def compare_intervention_reports(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    metrics: Sequence[str],
) -> dict[str, Any]:
    """Compare selected scalar metrics before and after an intervention."""

    deltas = {}
    for metric in metrics:
        left = _lookup_metric(before, metric)
        right = _lookup_metric(after, metric)
        deltas[metric] = {
            "before": left,
            "after": right,
            "delta": None if left is None or right is None else right - left,
        }
    return {
        "intervention_comparison_version": 2,
        "scientific_scope": INTERVENTION_SCOPE,
        "metric_deltas": deltas,
    }


def intervention_to_json(timeline: InterventionTimeline, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(timeline.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def _stage_at(timeline: InterventionTimeline, time_s: float) -> StagedIntervention:
    selected = timeline.stages[0]
    for stage in timeline.stages:
        if time_s >= stage.start_time_s:
            selected = stage
    return selected


def _lookup_metric(report: Mapping[str, Any], dotted_path: str) -> float | None:
    value: Any = report
    for part in dotted_path.split("."):
        if isinstance(value, Mapping) and part in value:
            value = value[part]
        else:
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _load_config(config: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(config, Mapping):
        return config
    return json.loads(Path(config).read_text(encoding="utf-8"))


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


__all__ = [
    "INTERVENTION_SCOPE",
    "InterventionDefinition",
    "InterventionTimeline",
    "ParameterSchedule",
    "StagedIntervention",
    "apply_intervention_parameters",
    "compare_intervention_reports",
    "intervention_from_config",
    "intervention_to_json",
    "replay_intervention",
]
