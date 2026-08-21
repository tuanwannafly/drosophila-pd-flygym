from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.experiments.healthy_baseline import HealthyBaselineConfig  # noqa: E402
from drosophila_pd.experiments.parameter_sweep import (  # noqa: E402
    ParameterSweepConfig,
    build_response_curves,
    load_parameter_sweep_config,
    run_parameter_sweep,
)


def test_sweep_config_parses_and_preserves_parameter_order():
    config = load_parameter_sweep_config(
        REPO_ROOT / "configs" / "experiments" / "sweeps" / "milestone_e1.yaml"
    )

    assert config.experiment_id == "milestone_e1_parameter_response"
    assert config.families[0].family == "motor_vigor_proxy"
    assert config.families[0].values == (1.0, 0.9, 0.8, 0.7, 0.6)
    assert config.families[1].family == "coordination_proxy"
    assert config.families[1].values == (1.0, 0.75, 0.5, 0.25, 0.0)


def test_sweep_condition_generation_marks_baseline_equivalent_conditions():
    config = _small_sweep_config()
    conditions = config.conditions()

    assert [condition.condition_id for condition in conditions] == [
        "motor_vigor_proxy_scale_100",
        "motor_vigor_proxy_scale_080",
        "coordination_proxy_scale_100",
        "coordination_proxy_scale_050",
    ]
    assert [condition.baseline_equivalent for condition in conditions] == [
        True,
        False,
        True,
        False,
    ]


def test_run_parameter_sweep_builds_combined_report_and_uses_fresh_calls():
    baseline_config = HealthyBaselineConfig.from_mapping({})
    sweep_config = _small_sweep_config()
    calls: list[str] = []

    report = run_parameter_sweep(
        baseline_config=baseline_config,
        sweep_config=sweep_config,
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner(calls),
    )

    assert calls == [
        "baseline",
        "motor_vigor_proxy_scale_100",
        "motor_vigor_proxy_scale_080",
        "coordination_proxy_scale_100",
        "coordination_proxy_scale_050",
    ]
    assert report["overall_pass"] is True
    assert report["checks"]["condition_count"]["pass"] is True
    assert len(report["conditions"]) == 4
    assert all(condition["controlled_variables"]["match"] for condition in report["conditions"])
    assert report["conditions"][0]["baseline_equivalence"]["pass"] is True
    assert report["response_curves"]["motor_vigor_proxy"]["condition_order"] == [
        "motor_vigor_proxy_scale_100",
        "motor_vigor_proxy_scale_080",
    ]


def test_parameter_sweep_records_partial_failures_without_discarding_successes():
    baseline_config = HealthyBaselineConfig.from_mapping({})
    sweep_config = _small_sweep_config()

    report = run_parameter_sweep(
        baseline_config=baseline_config,
        sweep_config=sweep_config,
        repo_root=REPO_ROOT,
        condition_runner=_fake_runner([], fail_condition="coordination_proxy_scale_050"),
    )

    statuses = {condition["condition_id"]: condition["status"] for condition in report["conditions"]}
    assert statuses["coordination_proxy_scale_050"] == "error"
    assert statuses["motor_vigor_proxy_scale_080"] == "completed"
    assert report["overall_pass"] is False
    assert report["checks"]["all_conditions_completed"]["pass"] is False
    assert "motor_vigor_proxy" in report["response_curves"]


def test_response_curve_reports_metric_deltas_and_monotonicity():
    conditions = [
        _completed_condition("motor_vigor_proxy_scale_100", "motor_vigor_proxy", 1.0, 6.0),
        _completed_condition("motor_vigor_proxy_scale_080", "motor_vigor_proxy", 0.8, 5.0),
        _completed_condition("motor_vigor_proxy_scale_060", "motor_vigor_proxy", 0.6, 4.0),
    ]

    curves = build_response_curves(conditions)
    displacement = curves["motor_vigor_proxy"]["metrics"]["planar_displacement_mm"]

    assert displacement["observed_monotonicity"] == "nonincreasing_in_config_order"
    assert displacement["points"][1]["absolute_delta"] == -1.0
    assert displacement["points"][1]["relative_delta"] == -1.0 / 6.0


def _small_sweep_config() -> ParameterSweepConfig:
    return ParameterSweepConfig.from_mapping(
        {
            "experiment_id": "milestone_e1_unit_test",
            "families": [
                {
                    "family": "motor_vigor_proxy",
                    "perturbation_type": "global_action_scale",
                    "parameter_name": "scale",
                    "baseline_equivalent_value": 1.0,
                    "values": [1.0, 0.8],
                },
                {
                    "family": "coordination_proxy",
                    "perturbation_type": "cpg_coupling_scale",
                    "parameter_name": "scale",
                    "baseline_equivalent_value": 1.0,
                    "values": [1.0, 0.5],
                },
            ],
        }
    )


def _fake_runner(calls: list[str], fail_condition: str | None = None):
    def runner(config, perturbation, condition_id):
        calls.append(condition_id)
        if condition_id == fail_condition:
            raise RuntimeError("synthetic condition failure")
        scale = 1.0
        perturbation_type = None
        if perturbation is not None:
            metadata = perturbation.metadata()
            perturbation_type = metadata["type"]
            scale = metadata["parameters"]["scale"]
        if perturbation_type == "global_action_scale":
            displacement = 6.0 * scale
            action_mean = 0.3 * scale
            action_abs_mean = 1.0 * scale
            transform = "global_action_scale"
            expected_scale = scale
        elif perturbation_type == "cpg_coupling_scale":
            displacement = 6.0 - (1.0 - scale)
            action_mean = 0.3
            action_abs_mean = 1.0
            transform = "identity"
            expected_scale = None
        else:
            displacement = 6.0
            action_mean = 0.3
            action_abs_mean = 1.0
            transform = "identity"
            expected_scale = None
        return _condition_report(
            displacement=displacement,
            action_mean=action_mean,
            action_abs_mean=action_abs_mean,
            perturbation_type=perturbation_type,
            expected_transform=transform,
            expected_scale=expected_scale,
        )

    return runner


def _completed_condition(
    condition_id: str,
    family: str,
    parameter_value: float,
    displacement: float,
) -> dict:
    baseline = _condition_report()
    condition = _condition_report(displacement=displacement)
    from drosophila_pd.metrics.comparison import compare_locomotion_reports

    return {
        "condition_id": condition_id,
        "family": family,
        "perturbation_type": "global_action_scale",
        "parameter_name": "scale",
        "parameter_value": parameter_value,
        "baseline_equivalent": parameter_value == 1.0,
        "status": "completed",
        "comparison": compare_locomotion_reports(baseline, condition),
    }


def _condition_report(
    *,
    displacement: float = 6.0,
    speed: float | None = None,
    yaw: float = 0.2,
    action_mean: float = 0.3,
    action_abs_mean: float = 1.0,
    perturbation_type: str | None = None,
    expected_transform: str = "identity",
    expected_scale: float | None = None,
) -> dict:
    speed = displacement * 2.0 if speed is None else speed
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
                    "mean": action_mean,
                    "initial": 0.1,
                    "final": 0.2,
                },
                "joint_angle_action_abs": {
                    "count": 210000,
                    "min": 0.0,
                    "max": 2.0,
                    "mean": action_abs_mean,
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
        "action_transformation_summary": {
            "perturbation_type": perturbation_type,
            "expected_transform": expected_transform,
            "expected_scale": expected_scale,
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
        },
    }
