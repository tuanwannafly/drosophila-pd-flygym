from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.metrics.comparison import (  # noqa: E402
    compare_locomotion_reports,
    evaluate_identity_equivalence,
)


def test_comparison_reports_scalar_and_adhesion_deltas():
    baseline = _condition_report()
    perturbed = _condition_report(displacement=8.0, speed=16.0, yaw=0.3)
    perturbed["derived_locomotion_metrics"]["controller_action_summary"]["adhesion"][
        "duty_factor_by_leg"
    ][0] = 0.7
    perturbed["derived_locomotion_metrics"]["controller_action_summary"]["adhesion"][
        "transition_count_by_leg"
    ][0] = 14

    comparison = compare_locomotion_reports(baseline, perturbed)

    assert comparison["scalars"]["planar_displacement_mm"]["absolute_delta"] == 2.0
    assert comparison["scalars"]["mean_planar_speed_mm_s"]["relative_delta"] == 0.6
    assert comparison["adhesion"]["duty_factor_delta_by_leg"][0] == pytest.approx(0.1)
    assert comparison["adhesion"]["transition_count_delta_by_leg"][0] == 2


def test_relative_delta_is_unavailable_near_zero_baseline():
    baseline = _condition_report(displacement=0.0)
    perturbed = _condition_report(displacement=1.0)

    comparison = compare_locomotion_reports(baseline, perturbed)

    assert comparison["scalars"]["planar_displacement_mm"]["relative_delta"] is None


def test_identity_equivalence_passes_for_identical_reports():
    baseline = _condition_report()
    perturbed = deepcopy(baseline)

    result = evaluate_identity_equivalence(baseline, perturbed)

    assert result["pass"] is True
    assert result["checks"]["final_thorax_position_mm"]["pass"] is True
    assert result["checks"]["adhesion_summary"]["pass"] is True


def test_identity_equivalence_fails_for_metric_difference():
    baseline = _condition_report()
    perturbed = _condition_report(displacement=6.1)

    result = evaluate_identity_equivalence(baseline, perturbed)

    assert result["pass"] is False
    assert result["checks"]["planar_displacement_mm"]["pass"] is False


def _condition_report(
    *, displacement: float = 6.0, speed: float = 10.0, yaw: float = 0.2
) -> dict:
    return {
        "overall_pass": True,
        "derived_locomotion_metrics": {
            "observations_are_finite": True,
            "derived_metrics_are_finite": True,
            "step_count": 5000,
            "final_thorax_position_mm": [displacement, 1.0, 1.0],
            "planar_displacement_mm": displacement,
            "mean_planar_speed_mm_s": speed,
            "heading_yaw_change_rad": yaw,
            "body_height_mm": {
                "count": 5001,
                "min": 0.8,
                "max": 1.2,
                "mean": 1.0,
                "initial": 1.1,
                "final": 1.0,
            },
            "controller_action_summary": {
                "joint_angle_action": {
                    "count": 210000,
                    "min": -2.0,
                    "max": 2.0,
                    "mean": 0.3,
                    "initial": 0.1,
                    "final": 0.2,
                },
                "joint_angle_action_abs": {
                    "count": 210000,
                    "min": 0.0,
                    "max": 2.0,
                    "mean": 1.0,
                    "initial": 0.1,
                    "final": 0.2,
                },
                "adhesion": {
                    "available": True,
                    "leg_order": ["lf", "lm", "lh", "rf", "rm", "rh"],
                    "duty_factor_by_leg": [0.6, 0.6, 0.6, 0.6, 0.6, 0.6],
                    "transition_count_by_leg": [12, 12, 12, 12, 12, 12],
                },
            },
        },
    }
