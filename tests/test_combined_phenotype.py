from __future__ import annotations

from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.experiments.combined_phenotype import (  # noqa: E402
    CombinedPhenotypeSweepConfig,
    build_interaction_analysis,
    load_combined_phenotype_sweep_config,
    run_combined_phenotype_sweep,
)
from drosophila_pd.experiments.healthy_baseline import HealthyBaselineConfig  # noqa: E402


def test_e2_config_parses_fixed_explicit_condition_matrix():
    config = load_combined_phenotype_sweep_config(
        REPO_ROOT / "configs" / "experiments" / "sweeps" / "milestone_e2.yaml"
    )

    assert config.experiment_id == "milestone_e2_combined_phenotype_characterization"
    assert [condition.condition_id for condition in config.conditions] == [
        "control_motor_100_coupling_100",
        "motor_080_coupling_100",
        "motor_070_coupling_100",
        "motor_060_coupling_100",
        "motor_100_coupling_075",
        "motor_100_coupling_050",
        "combined_motor_080_coupling_075",
        "combined_motor_070_coupling_075",
        "combined_motor_070_coupling_050",
    ]
    assert [condition.category for condition in config.conditions].count("combined") == 3
    assert config.conditions[0].baseline_equivalent is True


def test_e2_config_rejects_expanded_or_reordered_matrix():
    data = _raw_e2_mapping()
    data["conditions"] = list(reversed(data["conditions"]))

    with pytest.raises(ValueError, match="fixed compact condition matrix"):
        CombinedPhenotypeSweepConfig.from_mapping(data)


def test_run_combined_phenotype_sweep_builds_schema_and_fresh_calls():
    baseline_config = HealthyBaselineConfig.from_mapping({})
    sweep_config = load_combined_phenotype_sweep_config(
        REPO_ROOT / "configs" / "experiments" / "sweeps" / "milestone_e2.yaml"
    )
    calls: list[str] = []

    report = run_combined_phenotype_sweep(
        baseline_config=baseline_config,
        sweep_config=sweep_config,
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner(calls),
    )

    assert calls == ["baseline"] + [
        condition.condition_id for condition in sweep_config.conditions
    ]
    assert report["overall_pass"] is True
    assert report["checks"]["condition_count"]["pass"] is True
    assert len(report["conditions"]) == 9
    assert all(condition["controlled_variables"]["match"] for condition in report["conditions"])
    assert report["conditions"][0]["baseline_equivalence"]["pass"] is True
    assert report["conditions"][0]["perturbation"]["type"] == "composite"
    assert report["conditions"][0]["report"]["action_transformation_summary"][
        "effective_joint_angle_scale"
    ] == 1.0
    assert report["conditions"][0]["report"]["controller_transformation_summary"][
        "effective_cpg_coupling_scale"
    ] == 1.0
    assert len(report["interaction_analysis"]["combined_conditions"]) == 3
    assert "not establish" in report["scientific_scope"]


def test_interaction_analysis_reports_additive_residuals():
    baseline_config = HealthyBaselineConfig.from_mapping({})
    sweep_config = load_combined_phenotype_sweep_config(
        REPO_ROOT / "configs" / "experiments" / "sweeps" / "milestone_e2.yaml"
    )
    report = run_combined_phenotype_sweep(
        baseline_config=baseline_config,
        sweep_config=sweep_config,
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner([]),
    )

    combined = {
        item["condition_id"]: item
        for item in report["interaction_analysis"]["combined_conditions"]
    }
    displacement = combined["combined_motor_080_coupling_075"]["metrics"][
        "planar_displacement_mm"
    ]

    assert displacement["interaction_residual"] == pytest.approx(0.0)
    assert displacement["interaction_category"] == "approximately_additive"


def test_partial_condition_failure_is_recorded_without_dropping_successes():
    baseline_config = HealthyBaselineConfig.from_mapping({})
    sweep_config = load_combined_phenotype_sweep_config(
        REPO_ROOT / "configs" / "experiments" / "sweeps" / "milestone_e2.yaml"
    )

    report = run_combined_phenotype_sweep(
        baseline_config=baseline_config,
        sweep_config=sweep_config,
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner(
            [],
            fail_condition="motor_100_coupling_050",
        ),
    )

    statuses = {
        condition["condition_id"]: condition["status"]
        for condition in report["conditions"]
    }

    assert statuses["motor_100_coupling_050"] == "error"
    assert statuses["combined_motor_070_coupling_050"] == "completed"
    assert report["overall_pass"] is False
    assert report["checks"]["all_conditions_completed"]["pass"] is False
    combined_050 = [
        item
        for item in report["interaction_analysis"]["combined_conditions"]
        if item["condition_id"] == "combined_motor_070_coupling_050"
    ][0]
    assert combined_050["status"] == "unavailable"


def test_build_interaction_analysis_reports_super_additive_case():
    conditions = [
        _completed_condition("motor_070_coupling_100", "motor_only", 0.7, 1.0, 4.0),
        _completed_condition(
            "motor_100_coupling_050", "coordination_only", 1.0, 0.5, 5.0
        ),
        _completed_condition("combined_motor_070_coupling_050", "combined", 0.7, 0.5, 2.0),
    ]

    interaction = build_interaction_analysis(conditions)
    displacement = interaction["combined_conditions"][0]["metrics"][
        "planar_displacement_mm"
    ]

    assert displacement["expected_additive_delta"] == -3.0
    assert displacement["combined_delta"] == -4.0
    assert displacement["interaction_category"] == "super_additive"


def _fake_runner(calls: list[str], fail_condition: str | None = None):
    def runner(config, perturbation, condition_id):
        calls.append(condition_id)
        if condition_id == fail_condition:
            raise RuntimeError("synthetic E2 condition failure")
        motor_scale = 1.0
        coupling_scale = 1.0
        if perturbation is not None:
            for component in perturbation.metadata()["components"]:
                if component["type"] == "global_action_scale":
                    motor_scale = component["parameters"]["scale"]
                elif component["type"] == "cpg_coupling_scale":
                    coupling_scale = component["parameters"]["scale"]
        displacement = 6.0 + (motor_scale - 1.0) * 6.0 + (coupling_scale - 1.0)
        speed = displacement * 2.0
        yaw = 0.2 + (1.0 - coupling_scale) * 0.4
        height_shift = (1.0 - motor_scale) * 0.2
        report = _condition_report(
            displacement=displacement,
            speed=speed,
            yaw=yaw,
            height_min=0.8 + height_shift,
            height_max=1.2 + height_shift,
            height_mean=1.0 + height_shift,
            action_abs_mean=motor_scale,
        )
        if perturbation is not None:
            report["perturbation"] = perturbation.metadata()
            report["action_transformation_summary"] = _action_transform_summary(
                motor_scale=motor_scale
            )
            report["controller_transformation_summary"] = _controller_transform_summary(
                coupling_scale=coupling_scale
            )
        return report

    return runner


def _completed_condition(
    condition_id: str,
    category: str,
    motor_scale: float,
    coupling_scale: float,
    displacement: float,
) -> dict:
    from drosophila_pd.metrics.comparison import compare_locomotion_reports

    comparison = compare_locomotion_reports(_condition_report(), _condition_report(displacement=displacement))
    return {
        "condition_id": condition_id,
        "category": category,
        "motor_scale": motor_scale,
        "coupling_scale": coupling_scale,
        "status": "completed",
        "comparison": comparison,
    }


def _condition_report(
    *,
    displacement: float = 6.0,
    speed: float = 12.0,
    yaw: float = 0.2,
    height_min: float = 0.8,
    height_max: float = 1.2,
    height_mean: float = 1.0,
    action_abs_mean: float = 1.0,
) -> dict:
    path_length = displacement + abs(yaw) * 0.5
    return {
        "overall_pass": True,
        "derived_locomotion_metrics": {
            "observations_are_finite": True,
            "derived_metrics_are_finite": True,
            "step_count": 5000,
            "final_thorax_position_mm": [displacement, 1.0, height_mean],
            "planar_displacement_mm": displacement,
            "planar_path_length_mm": path_length,
            "trajectory_efficiency": displacement / path_length,
            "mean_planar_speed_mm_s": speed,
            "heading_yaw_change_rad": yaw,
            "body_height_mm": {
                "count": 5001,
                "min": height_min,
                "max": height_max,
                "mean": height_mean,
                "initial": height_mean,
                "final": height_mean,
            },
            "controller_action_summary": {
                "joint_angle_action": {
                    "count": 210000,
                    "min": -2.0 * action_abs_mean,
                    "max": 2.0 * action_abs_mean,
                    "mean": 0.3 * action_abs_mean,
                    "initial": 0.1 * action_abs_mean,
                    "final": 0.2 * action_abs_mean,
                },
                "joint_angle_action_abs": {
                    "count": 210000,
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


def _action_transform_summary(*, motor_scale: float) -> dict:
    return {
        "perturbation_type": "composite",
        "expected_transform": "composite_global_action_scale",
        "expected_scale": motor_scale,
        "effective_joint_angle_scale": motor_scale,
        "controller_joint_angle_shape": [5000, 42],
        "applied_joint_angle_shape": [5000, 42],
        "expected_joint_angle_count": 42,
        "action_dimensions_valid": True,
        "adhesion_commands_preserved": True,
        "joint_angle_transform_error_max": 0.0,
        "structural_checks": {
            "joint_angle_transform_matches_expected": {
                "expected": True,
                "observed": True,
                "pass": True,
            },
        },
    }


def _controller_transform_summary(*, coupling_scale: float) -> dict:
    return {
        "perturbation_type": "composite",
        "expected_transform": "composite_cpg_coupling_scale",
        "expected_cpg_coupling_scale": coupling_scale,
        "effective_cpg_coupling_scale": coupling_scale,
        "cpg_coupling_shape_before": [6, 6],
        "cpg_coupling_shape_after": [6, 6],
        "controller_dimensions_valid": True,
        "cpg_coupling_transform_error_max": 0.0,
        "structural_checks": {
            "cpg_coupling_transform_matches_expected": {
                "expected": True,
                "observed": True,
                "pass": True,
            },
        },
    }


def _raw_e2_mapping() -> dict:
    return {
        "experiment_id": "milestone_e2_combined_phenotype_characterization",
        "conditions": [
            {
                "condition_id": condition_id,
                "category": category,
                "motor_scale": motor_scale,
                "coupling_scale": coupling_scale,
            }
            for condition_id, category, motor_scale, coupling_scale in [
                ("control_motor_100_coupling_100", "control", 1.0, 1.0),
                ("motor_080_coupling_100", "motor_only", 0.8, 1.0),
                ("motor_070_coupling_100", "motor_only", 0.7, 1.0),
                ("motor_060_coupling_100", "motor_only", 0.6, 1.0),
                ("motor_100_coupling_075", "coordination_only", 1.0, 0.75),
                ("motor_100_coupling_050", "coordination_only", 1.0, 0.5),
                ("combined_motor_080_coupling_075", "combined", 0.8, 0.75),
                ("combined_motor_070_coupling_075", "combined", 0.7, 0.75),
                ("combined_motor_070_coupling_050", "combined", 0.7, 0.5),
            ]
        ],
    }
