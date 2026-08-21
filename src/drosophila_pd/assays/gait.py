"""Extensible gait assay interface over available rollout outputs."""

from __future__ import annotations

from typing import Any

import numpy as np

from drosophila_pd.assays.base import (
    IMPLEMENTED,
    PLANNED,
    AssayMetricSpec,
    AssayResult,
    BehavioralAssay,
    RolloutAssayInput,
)


GAIT_IMPLEMENTED_METRICS = (
    AssayMetricSpec(
        name="adhesion_duty_factor_by_leg",
        status=IMPLEMENTED,
        description="Fraction of samples with adhesion command active per leg.",
        required_inputs=("adhesion_outputs",),
        limitation="Adhesion duty factor is not a footfall-contact phase metric.",
    ),
    AssayMetricSpec(
        name="adhesion_transition_count_by_leg",
        status=IMPLEMENTED,
        description="Number of active/inactive adhesion transitions per leg.",
        required_inputs=("adhesion_outputs",),
        limitation="Transitions are command-state changes, not validated steps.",
    ),
)

GAIT_PLANNED_METRICS = (
    AssayMetricSpec(
        name="stance_swing_phase_by_leg",
        status=PLANNED,
        description="Per-leg stance and swing phase from contact or kinematic outputs.",
        required_inputs=("foot contact sensors", "leg kinematics"),
        limitation="Current rollout summaries do not provide contact-state arrays.",
    ),
    AssayMetricSpec(
        name="stride_length_and_frequency",
        status=PLANNED,
        description="Stride length, stride period, and stepping frequency.",
        required_inputs=("foot trajectories", "contact events"),
        limitation="Requires foot-level positions or contact events.",
    ),
    AssayMetricSpec(
        name="inter_leg_coordination_phase",
        status=PLANNED,
        description="Phase relationships across legs.",
        required_inputs=("per-leg gait events",),
        limitation="Adhesion summaries alone are insufficient for gait phase.",
    ),
    AssayMetricSpec(
        name="tripod_gait_regularization",
        status=PLANNED,
        description="Regularity of canonical tripod gait timing.",
        required_inputs=("per-leg gait events", "phase model"),
        limitation="Requires a prespecified gait-event extraction method.",
    ),
)


class GaitAssay(BehavioralAssay):
    """Report available adhesion-based summaries and planned gait metrics."""

    name = "gait"

    def specification(self) -> dict[str, Any]:
        return {
            "assay_name": self.name,
            "implemented_metrics": [
                metric.as_dict() for metric in GAIT_IMPLEMENTED_METRICS
            ],
            "planned_metrics": [metric.as_dict() for metric in GAIT_PLANNED_METRICS],
        }

    def evaluate(self, rollout: RolloutAssayInput) -> AssayResult:
        adhesion_outputs = rollout.adhesion_outputs
        if not adhesion_outputs:
            metrics = {
                "adhesion_outputs_available": False,
                "adhesion_duty_factor_by_leg": {},
                "adhesion_transition_count_by_leg": {},
                "implemented_gait_scope": (
                    "No adhesion outputs were supplied. Planned gait metrics "
                    "require additional contact or kinematic rollout outputs."
                ),
            }
        else:
            duty_factors: dict[str, float] = {}
            transition_counts: dict[str, int] = {}
            sample_counts: dict[str, int] = {}
            for leg, values in adhesion_outputs.items():
                array = np.asarray(values, dtype=float).ravel()
                if array.size == 0 or not np.isfinite(array).all():
                    raise ValueError("adhesion output arrays must be finite and non-empty.")
                active = array > 0.5
                duty_factors[str(leg)] = float(np.count_nonzero(active) / active.size)
                transition_counts[str(leg)] = int(np.count_nonzero(np.diff(active)))
                sample_counts[str(leg)] = int(active.size)
            metrics = {
                "adhesion_outputs_available": True,
                "adhesion_sample_count_by_leg": sample_counts,
                "adhesion_duty_factor_by_leg": duty_factors,
                "adhesion_transition_count_by_leg": transition_counts,
                "implemented_gait_scope": (
                    "Implemented metrics summarize adhesion command states only. "
                    "They are not validated footfall, stance, swing, or gait-phase "
                    "measurements."
                ),
            }
        return AssayResult(
            assay_name=self.name,
            metrics=metrics,
            implemented_metrics=GAIT_IMPLEMENTED_METRICS,
            planned_metrics=GAIT_PLANNED_METRICS,
        )


__all__ = [
    "GAIT_IMPLEMENTED_METRICS",
    "GAIT_PLANNED_METRICS",
    "GaitAssay",
]
