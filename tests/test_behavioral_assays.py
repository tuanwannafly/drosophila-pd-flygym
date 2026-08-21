from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.assays import (  # noqa: E402
    FreezingAssay,
    GaitAssay,
    OpenFieldAssay,
    RolloutAssayInput,
    TurningAssay,
    run_behavioral_assay_suite,
)


def test_open_field_assay_reports_trajectory_and_occupancy():
    rollout = _synthetic_rollout()
    result = OpenFieldAssay(
        {
            "arena_center_xy_mm": [0.0, 0.0],
            "arena_size_mm": [20.0, 20.0],
            "center_fraction": 0.5,
            "border_width_mm": 2.0,
            "grid_bins": 4,
        }
    ).evaluate(rollout)

    payload = result.as_dict()
    assert payload["assay_name"] == "open_field"
    assert payload["metrics"]["trajectory_visualization"]["sample_count"] == 5
    assert payload["metrics"]["center_occupancy"] == 0.8
    assert payload["metrics"]["border_occupancy"] == 0.2
    assert payload["metrics"]["exploration_index"] > 0


def test_freezing_assay_detects_pause_episodes():
    rollout = _synthetic_rollout()
    result = FreezingAssay(
        {
            "immobility_speed_threshold_mm_s": 0.5,
            "min_freezing_duration_s": 0.0,
        }
    ).evaluate(rollout)

    metrics = result.metrics
    assert metrics["pause_count"] == 1
    assert metrics["freezing_episode_count"] == 1
    assert metrics["pause_duration_s"] == 1.0
    assert metrics["immobility_ratio"] == 0.25
    assert metrics["pause_frequency_hz"] == 0.25


def test_turning_assay_reports_distribution_and_bias():
    rollout = _synthetic_rollout()
    result = TurningAssay(
        {
            "turn_rate_threshold_rad_s": 0.05,
            "min_turn_duration_s": 0.0,
            "turn_angle_histogram_bins": 4,
        }
    ).evaluate(rollout)

    metrics = result.metrics
    assert metrics["turn_bout_count"] == 1
    assert np.isclose(metrics["cumulative_turning_rad"], 0.6)
    assert np.isclose(metrics["left_right_bias"], 0.0)
    assert len(metrics["turn_angle_histogram"]["counts"]) == 4
    assert len(metrics["turn_angle_histogram"]["bin_edges_rad"]) == 5


def test_gait_assay_reports_adhesion_summaries_and_planned_metrics():
    rollout = _synthetic_rollout()
    result = GaitAssay().evaluate(rollout)

    payload = result.as_dict()
    metrics = payload["metrics"]
    assert metrics["adhesion_outputs_available"] is True
    assert metrics["adhesion_duty_factor_by_leg"]["LF"] == 0.6
    assert metrics["adhesion_transition_count_by_leg"]["LF"] == 2
    assert any(
        metric["name"] == "inter_leg_coordination_phase"
        for metric in payload["planned_metrics"]
    )


def test_gait_assay_is_explicit_when_adhesion_outputs_are_missing():
    rollout = RolloutAssayInput(
        thorax_positions=_positions(),
        thorax_quaternions=_yaw_quaternions([0.0, 0.1, 0.2, 0.3, 0.0]),
        timestep_s=1.0,
    )

    result = GaitAssay().evaluate(rollout)

    assert result.metrics["adhesion_outputs_available"] is False
    assert result.metrics["adhesion_duty_factor_by_leg"] == {}


def test_behavioral_assay_suite_runs_enabled_assays():
    rollout = _synthetic_rollout()
    results = run_behavioral_assay_suite(
        rollout=rollout,
        config={
            "open_field": {
                "arena_size_mm": [20.0, 20.0],
                "border_width_mm": 2.0,
            },
            "turning": {"turn_angle_histogram_bins": 4},
        },
    )

    assert results["assay_suite_version"] == 1
    assert set(results["assays"]) == {"open_field", "freezing", "turning", "gait"}
    assert "biological" in results["scientific_scope"]


def _synthetic_rollout() -> RolloutAssayInput:
    return RolloutAssayInput(
        thorax_positions=_positions(),
        thorax_quaternions=_yaw_quaternions([0.0, 0.1, 0.2, 0.3, 0.0]),
        timestep_s=1.0,
        adhesion_outputs={
            "LF": np.array([1, 1, 0, 0, 1]),
            "RF": np.array([0, 1, 1, 0, 0]),
        },
    )


def _positions() -> np.ndarray:
    return np.array(
        [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [2.0, 0.0, 1.0],
            [4.0, 0.0, 1.0],
            [9.0, 0.0, 1.0],
        ]
    )


def _yaw_quaternions(yaws: list[float]) -> np.ndarray:
    return np.array(
        [[np.cos(yaw / 2.0), 0.0, 0.0, np.sin(yaw / 2.0)] for yaw in yaws],
        dtype=float,
    )
