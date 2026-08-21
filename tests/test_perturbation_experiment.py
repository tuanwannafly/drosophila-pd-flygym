from __future__ import annotations

from copy import deepcopy
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.experiments.healthy_baseline import (  # noqa: E402
    HealthyBaselineConfig,
)
from drosophila_pd.experiments.perturbation_experiment import (  # noqa: E402
    build_controlled_variables,
    build_paired_checks,
    build_paired_perturbation_report,
    run_paired_perturbation_experiment,
)
from drosophila_pd.perturbations import (  # noqa: E402
    GlobalActionScalePerturbation,
    IdentityPerturbation,
)


def test_controlled_variables_capture_pairing_contract():
    config = HealthyBaselineConfig.from_mapping({})
    controlled = build_controlled_variables(config)

    assert controlled["random_seed"] == 0
    assert controlled["simulation"]["duration_s"] == 0.5
    assert controlled["world"]["type"] == "FlatGroundWorld"
    assert controlled["actuators"]["expected_actuated_dofs"] == 42
    assert controlled["skeleton"]["joint_preset"] == "JointPreset.LEGS_ONLY"


def test_identity_paired_report_requires_equivalence():
    config = HealthyBaselineConfig.from_mapping({})
    baseline = _condition_report()
    perturbed = deepcopy(baseline)
    perturbed["perturbation"] = IdentityPerturbation().metadata()

    report = build_paired_perturbation_report(
        baseline_config=config,
        perturbed_config=config,
        perturbation=IdentityPerturbation(),
        baseline_report=baseline,
        perturbed_report=perturbed,
        repo_root=REPO_ROOT,
    )

    assert report["identity_equivalence_pass"] is True
    assert report["checks"]["identity_equivalence_pass"]["pass"] is True
    assert report["paired_execution"]["fresh_fly_world_simulation_per_condition"] is True
    assert report["perturbed_config"]["experiment_id"] == config.experiment_id
    assert report["overall_pass"] is True
    assert "not a Parkinson" in report["scientific_scope"]


def test_identity_paired_report_fails_when_equivalence_fails():
    config = HealthyBaselineConfig.from_mapping({})
    baseline = _condition_report()
    perturbed = _condition_report(displacement=8.0)

    report = build_paired_perturbation_report(
        baseline_config=config,
        perturbed_config=config,
        perturbation=IdentityPerturbation(),
        baseline_report=baseline,
        perturbed_report=perturbed,
        repo_root=REPO_ROOT,
    )

    assert report["identity_equivalence_pass"] is False
    assert report["overall_pass"] is False


def test_action_scale_paired_report_checks_structure_not_effect_direction():
    config = HealthyBaselineConfig.from_mapping({})
    baseline = _condition_report()
    perturbed = _condition_report(displacement=8.0)
    perturbed["action_transformation_summary"] = _action_transform_summary(
        perturbation_type="global_action_scale",
        expected_scale=0.8,
    )

    report = build_paired_perturbation_report(
        baseline_config=config,
        perturbed_config=config,
        perturbation=GlobalActionScalePerturbation(scale=0.8),
        baseline_report=baseline,
        perturbed_report=perturbed,
        repo_root=REPO_ROOT,
    )

    assert report["identity_equivalence_pass"] is None
    assert "identity_equivalence_pass" not in report["checks"]
    assert report["checks"]["adhesion_commands_preserved"]["pass"] is True
    assert report["overall_pass"] is True
    assert report["comparison"]["scalars"]["planar_displacement_mm"][
        "absolute_delta"
    ] == 2.0


def test_controlled_variable_mismatch_fails_checks():
    baseline = _condition_report()
    perturbed = _condition_report()

    checks = build_paired_checks(
        baseline_report=baseline,
        perturbed_report=perturbed,
        perturbation_metadata=IdentityPerturbation().metadata(),
        controlled_variables_match=False,
        identity_equivalence_pass=True,
    )

    assert checks["controlled_variables_match"]["pass"] is False


def test_paired_perturbation_integration_with_real_flygym_if_available():
    _skip_unless_exact_colab_like_runtime()
    config = HealthyBaselineConfig.from_mapping(
        {
            "simulation": {
                "duration_s": 0.002,
                "warmup_duration_s": 0.0,
            }
        }
    )

    report = run_paired_perturbation_experiment(
        baseline_config=config,
        perturbation=IdentityPerturbation(),
        repo_root=REPO_ROOT,
    )

    assert report["overall_pass"]
    assert report["identity_equivalence_pass"] is True
    assert report["baseline"]["simulation_summary"]["step_count"] == 20


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
        "action_transformation_summary": _action_transform_summary(),
    }


def _action_transform_summary(
    *, perturbation_type: str | None = None, expected_scale: float | None = None
) -> dict:
    return {
        "perturbation_type": perturbation_type,
        "expected_transform": "identity"
        if perturbation_type != "global_action_scale"
        else "global_action_scale",
        "expected_scale": expected_scale,
        "controller_joint_angle_shape": [5000, 42],
        "applied_joint_angle_shape": [5000, 42],
        "expected_joint_angle_count": 42,
        "action_dimensions_valid": True,
        "adhesion_commands_preserved": True,
        "joint_angle_transform_error_max": 0.0,
        "joint_angle_transform_check": {
            "expected": True,
            "observed": True,
            "pass": True,
        },
        "structural_checks": {
            "action_dimensions_valid": {
                "expected": True,
                "observed": True,
                "pass": True,
            },
            "adhesion_commands_preserved": {
                "expected": True,
                "observed": True,
                "pass": True,
            },
            "joint_angle_transform_matches_expected": {
                "expected": True,
                "observed": True,
                "pass": True,
            },
        },
    }


def _skip_unless_exact_colab_like_runtime() -> None:
    try:
        flygym_version = version("flygym")
        mujoco_version = version("mujoco")
        import_module("flygym_demo")
    except (ModuleNotFoundError, PackageNotFoundError):
        pytest.skip("FlyGym paired perturbation integration is verified in Colab.")

    if sys.version_info[:2] != (3, 12):
        pytest.skip("Milestone D integration expects Python 3.12.")
    if flygym_version != "2.1.0" or mujoco_version != "3.9.0":
        pytest.skip("Milestone D integration expects FlyGym 2.1.0 and MuJoCo 3.9.0.")
