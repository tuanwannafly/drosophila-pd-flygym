"""Paired controlled perturbation experiments for Milestone D."""

from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from drosophila_pd.anatomy.audit import git_commit, runtime_environment
from drosophila_pd.experiments.healthy_baseline import (
    HealthyBaselineConfig,
    run_locomotion,
)
from drosophila_pd.metrics.comparison import (
    compare_locomotion_reports,
    evaluate_identity_equivalence,
)
from drosophila_pd.perturbations import (
    Perturbation,
    perturbation_metadata_complete,
)


SCIENTIFIC_SCOPE = (
    "This is a controlled simulation perturbation experiment. It is not a "
    "Parkinson's disease model and is not biological validation."
)


def run_paired_perturbation_experiment(
    *,
    baseline_config: HealthyBaselineConfig,
    perturbation: Perturbation,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Run baseline and perturbed conditions from fresh simulation state."""

    perturbed_config = perturbation.apply_to_config(baseline_config)
    baseline_report = run_locomotion(
        baseline_config,
        repo_root=repo_root,
        perturbation=None,
        condition_id="baseline",
        include_condition_metadata=True,
    )
    perturbed_report = run_locomotion(
        perturbed_config,
        repo_root=repo_root,
        perturbation=perturbation,
        condition_id="perturbed",
        include_condition_metadata=True,
        apply_config_perturbation=False,
    )
    return build_paired_perturbation_report(
        baseline_config=baseline_config,
        perturbed_config=perturbed_config,
        perturbation=perturbation,
        baseline_report=baseline_report,
        perturbed_report=perturbed_report,
        repo_root=repo_root,
    )


def build_paired_perturbation_report(
    *,
    baseline_config: HealthyBaselineConfig,
    perturbed_config: HealthyBaselineConfig,
    perturbation: Perturbation,
    baseline_report: dict[str, Any],
    perturbed_report: dict[str, Any],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable paired experiment report."""

    metadata = perturbation.metadata()
    baseline_controlled = build_controlled_variables(baseline_config)
    perturbed_controlled = build_controlled_variables(perturbed_config)
    controlled_variables_match = baseline_controlled == perturbed_controlled
    comparison = compare_locomotion_reports(baseline_report, perturbed_report)
    identity_equivalence = (
        evaluate_identity_equivalence(baseline_report, perturbed_report)
        if metadata["type"] == "identity"
        else None
    )
    identity_equivalence_pass = (
        identity_equivalence["pass"] if identity_equivalence is not None else None
    )
    checks = build_paired_checks(
        baseline_report=baseline_report,
        perturbed_report=perturbed_report,
        perturbation_metadata=metadata,
        controlled_variables_match=controlled_variables_match,
        identity_equivalence_pass=identity_equivalence_pass,
    )
    return {
        "experiment_id": f"milestone_d_{metadata['name']}",
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "baseline_config": baseline_config.to_report(),
        "perturbed_config": perturbed_config.to_report(),
        "perturbation": metadata,
        "paired_execution": {
            "baseline_condition_id": "baseline",
            "perturbed_condition_id": "perturbed",
            "fresh_fly_world_simulation_per_condition": True,
            "raw_trajectories_stored_in_report": False,
        },
        "controlled_variables": {
            "baseline": baseline_controlled,
            "perturbed": perturbed_controlled,
            "match": controlled_variables_match,
        },
        "baseline": baseline_report,
        "perturbed": perturbed_report,
        "comparison": comparison,
        "identity_equivalence": identity_equivalence,
        "identity_equivalence_pass": identity_equivalence_pass,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_controlled_variables(config: HealthyBaselineConfig) -> dict[str, Any]:
    """Return variables that must match for baseline-vs-perturbed pairing."""

    return {
        "random_seed": config.random_seed,
        "simulation": deepcopy(config.simulation),
        "world": deepcopy(config.world),
        "fly": deepcopy(config.fly),
        "actuators": deepcopy(config.actuators),
        "controller": config.controller.to_report(),
        "skeleton": {
            "joint_preset": "JointPreset.LEGS_ONLY",
            "axis_order": "AxisOrder.YAW_PITCH_ROLL",
        },
        "metric_definitions": {
            "locomotion_module": "drosophila_pd.metrics.locomotion",
            "comparison_module": "drosophila_pd.metrics.comparison",
        },
    }


def build_paired_checks(
    *,
    baseline_report: dict[str, Any],
    perturbed_report: dict[str, Any],
    perturbation_metadata: dict[str, Any],
    controlled_variables_match: bool,
    identity_equivalence_pass: bool | None,
) -> dict[str, dict[str, Any]]:
    """Build PASS/FAIL checks for a paired perturbation report."""

    baseline_metrics = baseline_report.get("derived_locomotion_metrics", {})
    perturbed_metrics = perturbed_report.get("derived_locomotion_metrics", {})
    perturbed_transform = perturbed_report.get("action_transformation_summary", {})
    structural_checks = perturbed_transform.get("structural_checks", {})

    checks = {
        "baseline_simulation_passed": _check(True, baseline_report.get("overall_pass")),
        "perturbed_simulation_passed": _check(
            True, perturbed_report.get("overall_pass")
        ),
        "controlled_variables_match": _check(True, controlled_variables_match),
        "perturbation_metadata_complete": _check(
            True, perturbation_metadata_complete(perturbation_metadata)
        ),
        "baseline_observations_finite": _check(
            True, baseline_metrics.get("observations_are_finite")
        ),
        "perturbed_observations_finite": _check(
            True, perturbed_metrics.get("observations_are_finite")
        ),
        "baseline_metrics_finite": _check(
            True, baseline_metrics.get("derived_metrics_are_finite")
        ),
        "perturbed_metrics_finite": _check(
            True, perturbed_metrics.get("derived_metrics_are_finite")
        ),
        "action_dimensions_valid": _check(
            True, perturbed_transform.get("action_dimensions_valid")
        ),
        "joint_angle_transform_matches_expected": _check(
            True,
            structural_checks.get(
                "joint_angle_transform_matches_expected", {}
            ).get("observed"),
        ),
    }
    if perturbation_metadata["type"] in {"identity", "global_action_scale"}:
        checks["adhesion_commands_preserved"] = _check(
            True, perturbed_transform.get("adhesion_commands_preserved")
        )
    if perturbation_metadata["type"] == "identity":
        checks["identity_equivalence_pass"] = _check(True, identity_equivalence_pass)
    return checks


def build_perturbation_unavailable_report(
    error: BaseException,
    *,
    baseline_config: HealthyBaselineConfig,
    perturbation: Perturbation,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a report for environments where FlyGym execution is unavailable."""

    return {
        "experiment_id": f"milestone_d_{perturbation.name}",
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "baseline_config": baseline_config.to_report(),
        "perturbation": perturbation.metadata(),
        "controlled_variables": {
            "baseline": build_controlled_variables(baseline_config),
            "perturbed": None,
            "match": False,
        },
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def _check(expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


__all__ = [
    "SCIENTIFIC_SCOPE",
    "build_controlled_variables",
    "build_paired_checks",
    "build_paired_perturbation_report",
    "build_perturbation_unavailable_report",
    "run_paired_perturbation_experiment",
]
