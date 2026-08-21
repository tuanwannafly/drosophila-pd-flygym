"""Comparison utilities for healthy/candidate/rescue rollout playback."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.measurement import measure_rollout_behavior
from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.behavior_platform.visualization import ViewerPlan, build_viewer_plan


@dataclass(frozen=True)
class ComparisonCondition:
    role: str
    rollout: RolloutData
    display_name: str | None = None

    def label(self) -> str:
        return self.display_name or self.role


@dataclass(frozen=True)
class ComparisonPlaybackPlan:
    conditions: tuple[str, ...]
    timeline: dict[str, Any]
    layout: str
    viewer_plans: Mapping[str, ViewerPlan]

    def as_dict(self) -> dict[str, Any]:
        return {
            "conditions": list(self.conditions),
            "timeline": dict(self.timeline),
            "layout": self.layout,
            "viewer_plans": {
                name: plan.as_dict() for name, plan in self.viewer_plans.items()
            },
        }


def compare_rollouts(
    conditions: Sequence[ComparisonCondition],
    *,
    measurement_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute synchronized behavioral summaries for multiple rollout roles."""

    normalized = _validate_conditions(conditions)
    measurements = {
        condition.role: measure_rollout_behavior(
            condition.rollout,
            config=measurement_config,
        )
        for condition in normalized
    }
    baseline_role = normalized[0].role
    baseline = measurements[baseline_role]
    comparisons = {
        role: _metric_deltas(baseline, measurement)
        for role, measurement in measurements.items()
        if role != baseline_role
    }
    return {
        "comparison_version": 2,
        "scientific_scope": (
            "Side-by-side behavioral comparison of existing rollouts only. "
            "Roles such as Healthy, Candidate, or Rescue are labels supplied by "
            "the caller and are not biological validation claims."
        ),
        "baseline_role": baseline_role,
        "roles": [condition.role for condition in normalized],
        "measurements": measurements,
        "deltas_from_baseline": comparisons,
        "synchronized_timeline": _timeline(normalized),
    }


def build_comparison_playback_plan(
    conditions: Sequence[ComparisonCondition],
    *,
    layout: str = "side_by_side",
) -> ComparisonPlaybackPlan:
    """Build a synchronized comparison viewer plan without opening viewers."""

    normalized = _validate_conditions(conditions)
    return ComparisonPlaybackPlan(
        conditions=tuple(condition.role for condition in normalized),
        timeline=_timeline(normalized),
        layout=layout,
        viewer_plans={
            condition.role: build_viewer_plan(condition.rollout)
            for condition in normalized
        },
    )


def _metric_deltas(
    baseline: dict[str, Any],
    condition: dict[str, Any],
) -> dict[str, float | None]:
    fields = {
        "path_length_mm": (
            baseline["path_geometry"]["path_length_mm"],
            condition["path_geometry"]["path_length_mm"],
        ),
        "planar_displacement_mm": (
            baseline["path_geometry"]["planar_displacement_mm"],
            condition["path_geometry"]["planar_displacement_mm"],
        ),
        "walking_duty_cycle": (
            baseline["walking_summary"]["walking_duty_cycle"],
            condition["walking_summary"]["walking_duty_cycle"],
        ),
        "cumulative_turning_rad": (
            baseline["turning_summary"]["cumulative_turning_rad"],
            condition["turning_summary"]["cumulative_turning_rad"],
        ),
        "tortuosity": (
            baseline["path_geometry"]["tortuosity"],
            condition["path_geometry"]["tortuosity"],
        ),
    }
    return {
        f"delta_{name}": None if base is None or value is None else float(value - base)
        for name, (base, value) in fields.items()
    }


def _timeline(conditions: Sequence[ComparisonCondition]) -> dict[str, Any]:
    sample_counts = {condition.role: condition.rollout.sample_count() for condition in conditions}
    timesteps = {condition.role: condition.rollout.timestep() for condition in conditions}
    return {
        "synchronized": len(set(timesteps.values())) == 1,
        "sample_counts": sample_counts,
        "timestep_s_by_role": timesteps,
        "duration_s_by_role": {
            role: (sample_count - 1) * timesteps[role]
            for role, sample_count in sample_counts.items()
        },
    }


def _validate_conditions(
    conditions: Sequence[ComparisonCondition],
) -> tuple[ComparisonCondition, ...]:
    result = tuple(conditions)
    if len(result) < 2:
        raise ValueError("at least two comparison conditions are required.")
    roles = [condition.role for condition in result]
    if len(set(roles)) != len(roles):
        raise ValueError("comparison condition roles must be unique.")
    return result


__all__ = [
    "ComparisonCondition",
    "ComparisonPlaybackPlan",
    "build_comparison_playback_plan",
    "compare_rollouts",
]
