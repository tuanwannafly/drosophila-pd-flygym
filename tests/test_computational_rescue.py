from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.experiments.computational_rescue import (  # noqa: E402
    COUPLING_PARTIAL_RESCUE_SCALE,
    CONTROL_COUPLING_SCALE,
    CONTROL_MOTOR_SCALE,
    ComputationalRescueConfig,
    MOTOR_PARTIAL_RESCUE_SCALE,
    PRIMARY_ENDPOINTS,
    REQUIRED_E5_CONDITION_MATRIX,
    RESCUE_CONDITION_IDS,
    build_recovery_fraction,
    classify_rescue_condition,
    load_computational_rescue_config,
    run_computational_rescue_validation,
)
from drosophila_pd.experiments.healthy_baseline import HealthyBaselineConfig  # noqa: E402


CONFIG_PATH = REPO_ROOT / "configs" / "experiments" / "validation" / "milestone_e5.yaml"


def test_e5_config_parses_exact_preregistered_matrix_and_midpoints():
    config = load_computational_rescue_config(CONFIG_PATH)

    assert config.experiment_id == "milestone_e5_preregistered_computational_rescue"
    assert config.seeds == (0, 1, 2, 3, 4)
    assert config.duration_s == 1.0
    assert tuple(
        (
            condition.condition_id,
            condition.category,
            condition.motor_scale,
            condition.coupling_scale,
        )
        for condition in config.conditions
    ) == REQUIRED_E5_CONDITION_MATRIX
    assert config.primary_endpoints == PRIMARY_ENDPOINTS
    assert config.frozen_states["selected_before_execution"] is True
    assert config.frozen_states["post_hoc_tuning_permitted"] is False
    assert (
        config.midpoint_derivation["motor_partial_rescue"]["midpoint_value"]
        == MOTOR_PARTIAL_RESCUE_SCALE
    )
    assert (
        config.midpoint_derivation["coupling_partial_rescue"]["midpoint_value"]
        == COUPLING_PARTIAL_RESCUE_SCALE
    )


def test_e5_config_rejects_tuned_rescue_parameters_or_posthoc_flags():
    tuned = _raw_e5_mapping()
    tuned["conditions"][2]["motor_scale"] = 0.91
    with pytest.raises(ValueError, match="fixed preregistered condition matrix"):
        ComputationalRescueConfig.from_mapping(tuned)

    midpoint = _raw_e5_mapping()
    midpoint["midpoint_derivation"]["motor_partial_rescue"]["midpoint_value"] = 0.91
    with pytest.raises(ValueError, match="motor partial rescue midpoint"):
        ComputationalRescueConfig.from_mapping(midpoint)

    posthoc = _raw_e5_mapping()
    posthoc["frozen_states"]["post_hoc_tuning_permitted"] = True
    with pytest.raises(ValueError, match="Post-hoc tuning"):
        ComputationalRescueConfig.from_mapping(posthoc)


def test_e5_recovery_fraction_math_and_zero_denominator_handling():
    partial = build_recovery_fraction(control=10.0, impaired=8.0, rescue=9.0)
    overshoot = build_recovery_fraction(control=10.0, impaired=8.0, rescue=11.0)
    worsened = build_recovery_fraction(control=10.0, impaired=8.0, rescue=7.0)
    zero = build_recovery_fraction(control=10.0, impaired=10.0, rescue=10.5)

    assert partial["recovery_fraction"] == pytest.approx(0.5)
    assert partial["direction_toward_control"] is True
    assert overshoot["recovery_fraction"] == pytest.approx(1.5)
    assert overshoot["no_farther_from_control"] is True
    assert worsened["recovery_fraction"] == pytest.approx(-0.5)
    assert worsened["direction_toward_control"] is False
    assert zero["recovery_fraction"] is None
    assert zero["denominator_near_zero"] is True


def test_e5_run_uses_all_conditions_per_seed_and_preserves_controls():
    baseline_config = HealthyBaselineConfig.from_mapping({})
    rescue_config = load_computational_rescue_config(CONFIG_PATH)
    calls: list[dict] = []

    report = run_computational_rescue_validation(
        baseline_config=baseline_config,
        rescue_config=rescue_config,
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner(calls),
    )

    assert baseline_config.duration_s == 0.5
    assert report["overall_pass"] is True
    assert len(report["seed_runs"]) == 5
    assert len(calls) == 30
    assert [call["seed"] for call in calls] == [
        seed
        for seed in (0, 1, 2, 3, 4)
        for _condition in rescue_config.conditions
    ]
    assert all(call["duration"] == 1.0 for call in calls)
    assert all(
        seed_run["full_restoration_reference_equivalence"]["pass"] is True
        for seed_run in report["seed_runs"]
    )
    assert report["full_restoration_reference_equivalence"]["pass"] is True
    assert all(
        condition["controlled_variables"]["match"] is True
        for seed_run in report["seed_runs"]
        for condition in seed_run["conditions"]
    )
    assert {
        condition_id: report["condition_assessments"][condition_id]["classification"]
        for condition_id in RESCUE_CONDITION_IDS
    } == {
        "motor_partial_rescue": "DIRECTIONALLY_RESCUED",
        "coordination_partial_rescue": "DIRECTIONALLY_RESCUED",
        "combined_partial_rescue": "DIRECTIONALLY_RESCUED",
    }
    assert "not an L-DOPA simulation" in report["scientific_scope"]


def test_e5_report_records_per_seed_recovery_and_reference_is_not_rescue_label():
    report = run_computational_rescue_validation(
        baseline_config=HealthyBaselineConfig.from_mapping({}),
        rescue_config=load_computational_rescue_config(CONFIG_PATH),
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner([]),
    )

    motor = report["condition_assessments"]["motor_partial_rescue"]
    reference = report["condition_assessments"][
        "full_computational_restoration_reference"
    ]

    assert motor["primary_endpoints"]["mean_planar_speed_mm_s"][
        "aggregate_direction_toward_control"
    ] is True
    assert motor["primary_endpoints"]["planar_path_length_mm"][
        "per_seed_direction_toward_control_count"
    ] == 5
    assert len(motor["per_seed"]) == 5
    assert reference["classification"] is None
    assert "not a rescue label" in reference["classification_scope"]


def test_e5_classification_semantics_are_conservative():
    stable_entries = [
        {"status": "completed", "overall_pass": True, "recovery": {}}
        for _ in range(5)
    ]

    rescued = _primary_aggregate(speed=True, path=True)
    mixed_endpoint = _primary_aggregate(speed=True, path=False)
    mixed_seed = _primary_aggregate(speed=True, path=True, speed_count=4)
    no_rescue = _primary_aggregate(speed=False, path=False)
    unstable_entries = deepcopy(stable_entries)
    unstable_entries[0]["status"] = "error"

    assert classify_rescue_condition(
        entries=stable_entries,
        primary_aggregate=rescued,
        expected_seed_count=5,
    ) == "DIRECTIONALLY_RESCUED"
    assert classify_rescue_condition(
        entries=stable_entries,
        primary_aggregate=mixed_endpoint,
        expected_seed_count=5,
    ) == "MIXED"
    assert classify_rescue_condition(
        entries=stable_entries,
        primary_aggregate=mixed_seed,
        expected_seed_count=5,
    ) == "MIXED"
    assert classify_rescue_condition(
        entries=stable_entries,
        primary_aggregate=no_rescue,
        expected_seed_count=5,
    ) == "NO_RESCUE"
    assert classify_rescue_condition(
        entries=unstable_entries,
        primary_aggregate=rescued,
        expected_seed_count=5,
    ) == "UNSTABLE"


def test_e5_partial_condition_failure_is_recorded_without_claiming_rescue():
    report = run_computational_rescue_validation(
        baseline_config=HealthyBaselineConfig.from_mapping({}),
        rescue_config=load_computational_rescue_config(CONFIG_PATH),
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner(
            [],
            fail_condition="seed_2_motor_partial_rescue",
        ),
    )

    assert report["overall_pass"] is False
    assert report["checks"]["all_conditions_completed"]["pass"] is False
    assert report["condition_assessments"]["motor_partial_rescue"][
        "classification"
    ] == "UNSTABLE"


def _fake_runner(calls: list[dict], *, fail_condition: str | None = None):
    def runner(config, perturbation, condition_id):
        calls.append(
            {
                "condition_id": condition_id,
                "seed": config.random_seed,
                "duration": config.duration_s,
                "has_perturbation": perturbation is not None,
            }
        )
        if condition_id == fail_condition:
            raise RuntimeError("synthetic E5 condition failure")
        motor_scale, coupling_scale = _scales_from_perturbation(perturbation)
        report = _condition_report(
            config=config,
            motor_scale=motor_scale,
            coupling_scale=coupling_scale,
        )
        if perturbation is not None:
            report["perturbation"] = perturbation.metadata()
            report["action_transformation_summary"] = _action_transform_summary(
                motor_scale
            )
            report["controller_transformation_summary"] = (
                _controller_transform_summary(coupling_scale)
            )
        return report

    return runner


def _scales_from_perturbation(perturbation) -> tuple[float, float]:
    motor_scale = CONTROL_MOTOR_SCALE
    coupling_scale = CONTROL_COUPLING_SCALE
    if perturbation is None:
        return motor_scale, coupling_scale
    for component in perturbation.metadata()["components"]:
        if component["type"] == "global_action_scale":
            motor_scale = component["parameters"]["scale"]
        elif component["type"] == "cpg_coupling_scale":
            coupling_scale = component["parameters"]["scale"]
    return motor_scale, coupling_scale


def _condition_report(*, config, motor_scale: float, coupling_scale: float) -> dict:
    factor = (float(motor_scale) + float(coupling_scale)) / 2.0
    baseline_speed = 20.0 + config.random_seed
    baseline_path = 30.0 + config.random_seed
    speed = baseline_speed * factor
    path = baseline_path * factor
    displacement = path * 0.7
    yaw = 0.1 + (1.0 - coupling_scale) * 0.2
    height_mean = 1.0 + (1.0 - motor_scale) * 0.5
    height_min = height_mean - 0.2
    height_max = height_mean + 0.2
    return {
        "overall_pass": True,
        "configuration": config.to_report(),
        "derived_locomotion_metrics": {
            "observations_are_finite": True,
            "derived_metrics_are_finite": True,
            "step_count": config.expected_step_count(),
            "final_thorax_position_mm": [displacement, 0.0, height_mean],
            "planar_displacement_mm": displacement,
            "planar_path_length_mm": path,
            "trajectory_efficiency": displacement / path,
            "mean_planar_speed_mm_s": speed,
            "heading_yaw_change_rad": yaw,
            "body_height_mm": {
                "count": config.expected_step_count() + 1,
                "min": height_min,
                "max": height_max,
                "mean": height_mean,
                "initial": height_mean,
                "final": height_mean,
            },
            "controller_action_summary": {
                "joint_angle_action": {
                    "count": config.expected_step_count() * 42,
                    "min": -2.0 * motor_scale,
                    "max": 2.0 * motor_scale,
                    "mean": 0.3 * motor_scale,
                    "initial": 0.1 * motor_scale,
                    "final": 0.2 * motor_scale,
                },
                "joint_angle_action_abs": {
                    "count": config.expected_step_count() * 42,
                    "min": 0.0,
                    "max": 2.0 * motor_scale,
                    "mean": motor_scale,
                    "initial": 0.1 * motor_scale,
                    "final": 0.2 * motor_scale,
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


def _action_transform_summary(motor_scale: float) -> dict:
    return {
        "effective_joint_angle_scale": motor_scale,
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


def _controller_transform_summary(coupling_scale: float) -> dict:
    return {
        "effective_cpg_coupling_scale": coupling_scale,
        "controller_dimensions_valid": True,
        "structural_checks": {
            "cpg_coupling_transform_matches_expected": {
                "expected": True,
                "observed": True,
                "pass": True,
            },
        },
    }


def _primary_aggregate(
    *,
    speed: bool,
    path: bool,
    speed_count: int = 5,
    path_count: int = 5,
) -> dict:
    return {
        "mean_planar_speed_mm_s": _aggregate_metric(speed, speed_count),
        "planar_path_length_mm": _aggregate_metric(path, path_count),
    }


def _aggregate_metric(direction: bool, direction_count: int) -> dict:
    return {
        "aggregate_direction_toward_control": direction,
        "aggregate_no_farther_from_control": direction,
        "per_seed_direction_toward_control_count": direction_count,
        "count": 5,
    }


def _raw_e5_mapping() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)
