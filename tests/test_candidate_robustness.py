from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.experiments.candidate_robustness import (  # noqa: E402
    CandidateRobustnessConfig,
    build_sign_consistency,
    load_candidate_robustness_config,
    run_candidate_robustness_validation,
)
from drosophila_pd.experiments.healthy_baseline import HealthyBaselineConfig  # noqa: E402


def test_e3_config_parses_seed_duration_and_frozen_candidate():
    config = load_candidate_robustness_config(
        REPO_ROOT / "configs" / "experiments" / "validation" / "milestone_e3.yaml"
    )

    assert config.experiment_id == "milestone_e3_candidate_robustness"
    assert config.seeds == (0, 1, 2, 3, 4)
    assert config.duration_s == 1.0
    assert config.candidate.motor_scale == 0.8
    assert config.candidate.coupling_scale == 0.75
    assert config.candidate.selected_before_e3_execution is True
    assert config.candidate.post_hoc_tuning_permitted is False


def test_e3_config_rejects_candidate_tuning():
    data = _raw_e3_mapping()
    data["candidate"]["motor_scale"] = 0.7

    with pytest.raises(ValueError, match="motor_scale must remain frozen"):
        CandidateRobustnessConfig.from_mapping(data)


def test_e3_config_rejects_seed_or_duration_drift():
    seed_data = _raw_e3_mapping()
    seed_data["validation_design"]["seeds"] = [0, 1]
    with pytest.raises(ValueError, match="seed set"):
        CandidateRobustnessConfig.from_mapping(seed_data)

    duration_data = _raw_e3_mapping()
    duration_data["validation_design"]["duration_s"] = 0.5
    with pytest.raises(ValueError, match="duration_s"):
        CandidateRobustnessConfig.from_mapping(duration_data)


def test_e3_run_uses_same_seed_pairs_and_does_not_mutate_baseline_config():
    baseline_config = HealthyBaselineConfig.from_mapping({})
    validation_config = CandidateRobustnessConfig.from_mapping(_raw_e3_mapping())
    calls: list[dict] = []

    report = run_candidate_robustness_validation(
        baseline_config=baseline_config,
        validation_config=validation_config,
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner(calls),
    )

    assert baseline_config.duration_s == 0.5
    assert baseline_config.random_seed == 0
    assert report["overall_pass"] is True
    assert report["robustness_assessment"]["classification"] == "ROBUST"
    assert len(report["pairs"]) == 5
    assert [call["seed"] for call in calls] == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]
    assert all(call["duration"] == 1.0 for call in calls)
    assert all(pair["same_seed_within_pair"] for pair in report["pairs"])
    assert all(pair["controlled_variables"]["match"] for pair in report["pairs"])
    assert all(
        pair["candidate"]["configuration"]["random_seed"]
        == pair["baseline"]["configuration"]["random_seed"]
        for pair in report["pairs"]
    )


def test_e3_report_contains_aggregate_statistics_and_sign_consistency():
    report = run_candidate_robustness_validation(
        baseline_config=HealthyBaselineConfig.from_mapping({}),
        validation_config=CandidateRobustnessConfig.from_mapping(_raw_e3_mapping()),
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner([]),
    )

    speed_delta = report["aggregate_statistics"]["metrics"][
        "mean_planar_speed_mm_s"
    ]["absolute_delta"]
    sign = report["sign_consistency"]

    assert speed_delta["count"] == 5
    assert speed_delta["mean"] == pytest.approx(-2.0)
    assert speed_delta["std"] == pytest.approx(0.0)
    assert sign["number_of_seeds_negative_speed_delta"] == 5
    assert sign["number_of_seeds_negative_displacement_delta"] == 5
    assert sign["metrics"]["yaw_abs_change_delta"]["positive"] == 5
    assert "scientific_scope" in report
    assert "not establish" in report["scientific_scope"]


def test_e3_mixed_classification_when_locomotor_direction_varies():
    report = run_candidate_robustness_validation(
        baseline_config=HealthyBaselineConfig.from_mapping({}),
        validation_config=CandidateRobustnessConfig.from_mapping(_raw_e3_mapping()),
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner([], mixed_seed=3),
    )

    assert report["overall_pass"] is True
    assert report["robustness_assessment"]["classification"] == "MIXED"
    assert report["sign_consistency"]["number_of_seeds_negative_speed_delta"] == 4


def test_e3_partial_failure_is_recorded_and_classified_unstable():
    report = run_candidate_robustness_validation(
        baseline_config=HealthyBaselineConfig.from_mapping({}),
        validation_config=CandidateRobustnessConfig.from_mapping(_raw_e3_mapping()),
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner([], fail_condition="seed_2_candidate_motor_080_coupling_075"),
    )

    statuses = {pair["seed"]: pair["status"] for pair in report["pairs"]}

    assert statuses[2] == "error"
    assert report["overall_pass"] is False
    assert report["checks"]["all_seed_pairs_completed"]["pass"] is False
    assert report["robustness_assessment"]["classification"] == "UNSTABLE"


def test_build_sign_consistency_counts_selected_delta_signs():
    pairs = [
        _completed_pair(speed_delta=-1.0, displacement_delta=-0.5, efficiency_delta=-0.1, yaw_abs_delta=0.2),
        _completed_pair(speed_delta=0.5, displacement_delta=-0.25, efficiency_delta=0.0, yaw_abs_delta=-0.1),
    ]

    sign = build_sign_consistency(pairs)

    assert sign["number_of_seeds_negative_speed_delta"] == 1
    assert sign["number_of_seeds_negative_displacement_delta"] == 2
    assert sign["number_of_seeds_negative_trajectory_efficiency_delta"] == 1
    assert sign["number_of_seeds_positive_yaw_abs_change_delta"] == 1


def _fake_runner(
    calls: list[dict],
    *,
    fail_condition: str | None = None,
    mixed_seed: int | None = None,
):
    def runner(config, perturbation, condition_id):
        seed = config.random_seed
        calls.append(
            {
                "condition_id": condition_id,
                "seed": seed,
                "duration": config.duration_s,
                "has_perturbation": perturbation is not None,
            }
        )
        if condition_id == fail_condition:
            raise RuntimeError("synthetic E3 condition failure")

        baseline_displacement = 10.0 + seed
        baseline_speed = 20.0 + seed
        baseline_yaw = 0.1 * (seed + 1)
        if perturbation is None:
            return _condition_report(
                config=config,
                displacement=baseline_displacement,
                speed=baseline_speed,
                yaw=baseline_yaw,
                action_abs_mean=1.0,
            )

        speed_delta = 1.0 if seed == mixed_seed else -2.0
        displacement_delta = 0.5 if seed == mixed_seed else -1.0
        report = _condition_report(
            config=config,
            displacement=baseline_displacement + displacement_delta,
            speed=baseline_speed + speed_delta,
            yaw=baseline_yaw + 0.05,
            action_abs_mean=0.8,
        )
        report["perturbation"] = perturbation.metadata()
        report["action_transformation_summary"] = _action_transform_summary()
        report["controller_transformation_summary"] = _controller_transform_summary()
        return report

    return runner


def _condition_report(
    *,
    config,
    displacement: float,
    speed: float,
    yaw: float,
    action_abs_mean: float,
) -> dict:
    path_length = displacement + abs(yaw)
    return {
        "overall_pass": True,
        "configuration": config.to_report(),
        "derived_locomotion_metrics": {
            "observations_are_finite": True,
            "derived_metrics_are_finite": True,
            "step_count": config.expected_step_count(),
            "final_thorax_position_mm": [displacement, 0.0, 1.0],
            "planar_displacement_mm": displacement,
            "planar_path_length_mm": path_length,
            "trajectory_efficiency": displacement / path_length,
            "mean_planar_speed_mm_s": speed,
            "heading_yaw_change_rad": yaw,
            "body_height_mm": {
                "count": config.expected_step_count() + 1,
                "min": 0.8,
                "max": 1.2,
                "mean": 1.0,
                "initial": 1.0,
                "final": 1.0,
            },
            "controller_action_summary": {
                "joint_angle_action": {
                    "count": config.expected_step_count() * 42,
                    "min": -2.0 * action_abs_mean,
                    "max": 2.0 * action_abs_mean,
                    "mean": 0.3 * action_abs_mean,
                    "initial": 0.1 * action_abs_mean,
                    "final": 0.2 * action_abs_mean,
                },
                "joint_angle_action_abs": {
                    "count": config.expected_step_count() * 42,
                    "min": 0.0,
                    "max": 2.0 * action_abs_mean,
                    "mean": action_abs_mean,
                    "initial": 0.1 * action_abs_mean,
                    "final": 0.2 * action_abs_mean,
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


def _action_transform_summary() -> dict:
    return {
        "effective_joint_angle_scale": 0.8,
        "action_dimensions_valid": True,
        "adhesion_commands_preserved": True,
        "structural_checks": {
            "joint_angle_transform_matches_expected": {
                "expected": True,
                "observed": True,
                "pass": True,
            },
        },
    }


def _controller_transform_summary() -> dict:
    return {
        "effective_cpg_coupling_scale": 0.75,
        "controller_dimensions_valid": True,
        "structural_checks": {
            "cpg_coupling_transform_matches_expected": {
                "expected": True,
                "observed": True,
                "pass": True,
            },
        },
    }


def _completed_pair(
    *,
    speed_delta: float,
    displacement_delta: float,
    efficiency_delta: float,
    yaw_abs_delta: float,
) -> dict:
    return {
        "status": "completed",
        "key_metrics": {
            "mean_planar_speed_mm_s": {"absolute_delta": speed_delta},
            "planar_displacement_mm": {"absolute_delta": displacement_delta},
            "trajectory_efficiency": {"absolute_delta": efficiency_delta},
            "heading_yaw_abs_change_rad": {"absolute_delta": yaw_abs_delta},
        },
    }


def _raw_e3_mapping() -> dict:
    return {
        "experiment_id": "milestone_e3_candidate_robustness",
        "validation_design": {
            "duration_s": 1.0,
            "seeds": [0, 1, 2, 3, 4],
            "rendering_required": False,
        },
        "candidate": {
            "motor_scale": 0.8,
            "coupling_scale": 0.75,
            "preregistered_parameter_source": (
                "Milestone E2 combined phenotype characterization"
            ),
            "selected_before_e3_execution": True,
            "post_hoc_tuning_permitted": False,
        },
    }
