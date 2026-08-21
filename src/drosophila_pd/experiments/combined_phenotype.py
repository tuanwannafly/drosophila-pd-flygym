"""Combined proxy characterization for Milestone E2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import math
from pathlib import Path
from typing import Any, Callable

import yaml

from drosophila_pd.anatomy.audit import git_commit, runtime_environment
from drosophila_pd.experiments.healthy_baseline import (
    HealthyBaselineConfig,
    run_locomotion,
)
from drosophila_pd.experiments.perturbation_experiment import (
    build_controlled_variables,
)
from drosophila_pd.metrics.comparison import (
    compare_locomotion_reports,
    evaluate_identity_equivalence,
)
from drosophila_pd.perturbations import (
    CPGCouplingScalePerturbation,
    CompositePerturbation,
    GlobalActionScalePerturbation,
    Perturbation,
    perturbation_metadata_complete,
)


SCIENTIFIC_SCOPE = (
    "Milestone E2 characterizes combined phenomenological simulation "
    "perturbations. It does not establish a mechanistic or validated "
    "Parkinson's disease model and is not biological validation."
)

LITERATURE_GROUNDING_SUMMARY = {
    "supported_background": [
        "Drosophila neural dopamine deficiency is associated with reduced "
        "spontaneous locomotor speed and distance.",
        "Drosophila alpha-synuclein and Parkinson-related models show locomotor "
        "impairment.",
        "Some larval alpha-synuclein models show altered angular velocity, pause "
        "behavior, and navigation.",
    ],
    "unsupported_mapping": (
        "No established direct mapping is encoded from dopamine concentration or "
        "dopaminergic neuron loss to a FlyGym action scale or CPG coupling scale."
    ),
}

REQUIRED_CONDITION_MATRIX = (
    ("control_motor_100_coupling_100", "control", 1.0, 1.0),
    ("motor_080_coupling_100", "motor_only", 0.8, 1.0),
    ("motor_070_coupling_100", "motor_only", 0.7, 1.0),
    ("motor_060_coupling_100", "motor_only", 0.6, 1.0),
    ("motor_100_coupling_075", "coordination_only", 1.0, 0.75),
    ("motor_100_coupling_050", "coordination_only", 1.0, 0.5),
    ("combined_motor_080_coupling_075", "combined", 0.8, 0.75),
    ("combined_motor_070_coupling_075", "combined", 0.7, 0.75),
    ("combined_motor_070_coupling_050", "combined", 0.7, 0.5),
)

PRIMARY_METRICS = (
    "planar_displacement_mm",
    "mean_planar_speed_mm_s",
    "heading_yaw_change_rad",
    "body_height_min_mm",
    "body_height_mean_mm",
    "body_height_range_mm",
    "joint_angle_action_abs_mean",
    "planar_path_length_mm",
    "trajectory_efficiency",
)

INTERACTION_TOLERANCE = 0.15

ConditionRunner = Callable[
    [HealthyBaselineConfig, Perturbation | None, str], dict[str, Any]
]


@dataclass(frozen=True)
class CombinedPhenotypeConditionSpec:
    """One explicit Milestone E2 condition."""

    condition_id: str
    category: str
    motor_scale: float
    coupling_scale: float
    description: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CombinedPhenotypeConditionSpec":
        condition = cls(
            condition_id=_require_name(data, "condition_id"),
            category=_require_name(data, "category"),
            motor_scale=_finite_nonnegative_float(
                data.get("motor_scale"), "motor_scale"
            ),
            coupling_scale=_finite_nonnegative_float(
                data.get("coupling_scale"), "coupling_scale"
            ),
            description=data.get("description"),
        )
        condition.validate()
        return condition

    @property
    def baseline_equivalent(self) -> bool:
        return math.isclose(self.motor_scale, 1.0, abs_tol=1e-12) and math.isclose(
            self.coupling_scale, 1.0, abs_tol=1e-12
        )

    def validate(self) -> None:
        if self.category not in {
            "control",
            "motor_only",
            "coordination_only",
            "combined",
        }:
            raise ValueError(f"Unsupported E2 condition category: {self.category}")
        _reject_condition_mapping_terms(self.condition_id)
        _reject_condition_mapping_terms(self.category)

    def perturbation(self, *, experiment_id: str) -> CompositePerturbation:
        return CompositePerturbation(
            name=self.condition_id,
            config_id=experiment_id,
            components=(
                CPGCouplingScalePerturbation(
                    scale=self.coupling_scale,
                    name=f"{self.condition_id}_coordination_proxy",
                    config_id=experiment_id,
                ),
                GlobalActionScalePerturbation(
                    scale=self.motor_scale,
                    name=f"{self.condition_id}_motor_vigor_proxy",
                    config_id=experiment_id,
                ),
            ),
        )

    def to_report(self, *, experiment_id: str) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "category": self.category,
            "motor_scale": self.motor_scale,
            "coupling_scale": self.coupling_scale,
            "baseline_equivalent": self.baseline_equivalent,
            "description": self.description,
            "intervention_order": ["cpg_coupling_scale", "global_action_scale"],
            "perturbation": self.perturbation(
                experiment_id=experiment_id
            ).metadata(),
        }


@dataclass(frozen=True)
class CombinedPhenotypeSweepConfig:
    """Validated explicit-condition Milestone E2 configuration."""

    experiment_id: str
    conditions: tuple[CombinedPhenotypeConditionSpec, ...]
    scientific_frame: dict[str, Any]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CombinedPhenotypeSweepConfig":
        raw_conditions = data.get("conditions")
        if not isinstance(raw_conditions, list) or not raw_conditions:
            raise ValueError("E2 sweep configuration requires explicit conditions.")
        config = cls(
            experiment_id=_require_name(data, "experiment_id"),
            conditions=tuple(
                CombinedPhenotypeConditionSpec.from_mapping(item)
                for item in raw_conditions
            ),
            scientific_frame=dict(data.get("scientific_frame") or {}),
        )
        config.validate()
        return config

    def validate(self) -> None:
        condition_ids = [condition.condition_id for condition in self.conditions]
        if len(set(condition_ids)) != len(condition_ids):
            raise ValueError("E2 condition IDs must be unique.")
        observed = tuple(
            (
                condition.condition_id,
                condition.category,
                condition.motor_scale,
                condition.coupling_scale,
            )
            for condition in self.conditions
        )
        if observed != REQUIRED_CONDITION_MATRIX:
            raise ValueError(
                "Milestone E2 uses the fixed compact condition matrix; do not "
                "expand or reorder it without explicit authorization."
            )

    def to_report(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "conditions": [
                condition.to_report(experiment_id=self.experiment_id)
                for condition in self.conditions
            ],
            "scientific_frame": self.scientific_frame,
            "condition_matrix_policy": "fixed_explicit_compact_matrix",
        }


def load_combined_phenotype_sweep_config(
    path: str | Path,
) -> CombinedPhenotypeSweepConfig:
    """Load a Milestone E2 YAML configuration file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("E2 sweep configuration root must be a mapping.")
    return CombinedPhenotypeSweepConfig.from_mapping(loaded)


def run_combined_phenotype_sweep(
    *,
    baseline_config: HealthyBaselineConfig,
    sweep_config: CombinedPhenotypeSweepConfig,
    repo_root: str | Path | None = None,
    condition_runner: ConditionRunner | None = None,
) -> dict[str, Any]:
    """Run baseline once, then every explicit E2 condition from fresh state."""

    runner = condition_runner or _default_condition_runner(repo_root=repo_root)
    baseline_report = runner(baseline_config, None, "baseline")
    conditions = [
        _run_condition(
            baseline_config=baseline_config,
            baseline_report=baseline_report,
            sweep_config=sweep_config,
            spec=spec,
            runner=runner,
        )
        for spec in sweep_config.conditions
    ]
    return build_combined_phenotype_report(
        baseline_config=baseline_config,
        sweep_config=sweep_config,
        baseline_report=baseline_report,
        conditions=conditions,
        repo_root=repo_root,
    )


def build_combined_phenotype_report(
    *,
    baseline_config: HealthyBaselineConfig,
    sweep_config: CombinedPhenotypeSweepConfig,
    baseline_report: dict[str, Any],
    conditions: list[dict[str, Any]],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the JSON-serializable Milestone E2 characterization report."""

    checks = build_combined_checks(
        baseline_report=baseline_report,
        conditions=conditions,
        expected_condition_count=len(sweep_config.conditions),
    )
    return {
        "experiment_id": sweep_config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "literature_grounding_summary": LITERATURE_GROUNDING_SUMMARY,
        "baseline_config": baseline_config.to_report(),
        "sweep_config": sweep_config.to_report(),
        "source_api_findings": _source_api_findings(),
        "paired_execution": {
            "baseline_condition_id": "baseline",
            "fresh_fly_world_simulation_per_condition": True,
            "raw_trajectories_stored_in_report": False,
            "gpu_or_rendering_required": False,
        },
        "controlled_variables": {
            "baseline": build_controlled_variables(baseline_config),
            "preserved_except_declared_proxies": True,
            "declared_proxy_variables": ["motor_scale", "coupling_scale"],
        },
        "baseline": baseline_report,
        "conditions": conditions,
        "interaction_analysis": build_interaction_analysis(conditions),
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_combined_phenotype_unavailable_report(
    error: BaseException,
    *,
    baseline_config: HealthyBaselineConfig,
    sweep_config: CombinedPhenotypeSweepConfig,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a report for environments where FlyGym execution is unavailable."""

    return {
        "experiment_id": sweep_config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "literature_grounding_summary": LITERATURE_GROUNDING_SUMMARY,
        "baseline_config": baseline_config.to_report(),
        "sweep_config": sweep_config.to_report(),
        "conditions": [],
        "interaction_analysis": {},
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_interaction_analysis(conditions: list[dict[str, Any]]) -> dict[str, Any]:
    """Compare combined effects with the sum of single-proxy effects."""

    completed_by_scale = {
        _scale_key(condition["motor_scale"], condition["coupling_scale"]): condition
        for condition in conditions
        if condition.get("status") == "completed"
    }
    results = []
    for condition in conditions:
        if condition.get("status") != "completed" or condition.get("category") != "combined":
            continue
        motor_ref = completed_by_scale.get(_scale_key(condition["motor_scale"], 1.0))
        coordination_ref = completed_by_scale.get(
            _scale_key(1.0, condition["coupling_scale"])
        )
        if motor_ref is None or coordination_ref is None:
            results.append(
                {
                    "condition_id": condition["condition_id"],
                    "status": "unavailable",
                    "reason": "missing single-proxy reference condition",
                    "motor_reference_condition_id": (
                        motor_ref["condition_id"] if motor_ref is not None else None
                    ),
                    "coordination_reference_condition_id": (
                        coordination_ref["condition_id"]
                        if coordination_ref is not None
                        else None
                    ),
                }
            )
            continue
        results.append(
            {
                "condition_id": condition["condition_id"],
                "status": "completed",
                "motor_scale": condition["motor_scale"],
                "coupling_scale": condition["coupling_scale"],
                "definition": (
                    "interaction_residual = combined_delta - "
                    "(motor_only_delta + coordination_only_delta)"
                ),
                "categorical_tolerance": INTERACTION_TOLERANCE,
                "motor_reference_condition_id": motor_ref["condition_id"],
                "coordination_reference_condition_id": coordination_ref["condition_id"],
                "metrics": {
                    metric: _interaction_metric(
                        combined=condition,
                        motor_only=motor_ref,
                        coordination_only=coordination_ref,
                        metric=metric,
                    )
                    for metric in PRIMARY_METRICS
                    if _comparison_has_metric(condition, metric)
                    and _comparison_has_metric(motor_ref, metric)
                    and _comparison_has_metric(coordination_ref, metric)
                },
            }
        )
    return {
        "definition": (
            "For each combined condition, metric deltas relative to the baseline "
            "are compared with the sum of the matching motor-only and "
            "coordination-only deltas."
        ),
        "categorical_tolerance": INTERACTION_TOLERANCE,
        "combined_conditions": results,
    }


def build_condition_characterization(comparison: dict[str, Any]) -> dict[str, Any]:
    """Build descriptive computational phenotype fields from metric deltas."""

    displacement = _scalar(comparison, "planar_displacement_mm")
    speed = _scalar(comparison, "mean_planar_speed_mm_s")
    yaw = _scalar(comparison, "heading_yaw_change_rad")
    height_min = _scalar(comparison, "body_height_min_mm")
    height_mean = _scalar(comparison, "body_height_mean_mm")
    height_range = _scalar(comparison, "body_height_range_mm")
    action_abs = _scalar(comparison, "joint_angle_action_abs_mean")
    return {
        "locomotor_output_change": {
            "planar_displacement_relative_delta": displacement.get("relative_delta"),
            "mean_speed_relative_delta": speed.get("relative_delta"),
            "descriptor": _relative_change_label(speed.get("relative_delta")),
        },
        "directional_change": {
            "yaw_absolute_delta_rad": yaw.get("absolute_delta"),
            "yaw_relative_delta": yaw.get("relative_delta"),
            "descriptor": _magnitude_label(
                yaw.get("relative_delta"),
                fallback_absolute_delta=yaw.get("absolute_delta"),
            ),
        },
        "postural_change": {
            "height_min_relative_delta": height_min.get("relative_delta"),
            "height_mean_relative_delta": height_mean.get("relative_delta"),
            "height_range_relative_delta": height_range.get("relative_delta"),
            "descriptor": _magnitude_label(height_mean.get("relative_delta")),
        },
        "action_change": {
            "joint_action_abs_mean_relative_delta": action_abs.get("relative_delta"),
            "descriptor": _relative_change_label(action_abs.get("relative_delta")),
        },
        "descriptive_class": _descriptive_class(
            displacement=displacement,
            speed=speed,
            yaw=yaw,
            height_mean=height_mean,
            height_range=height_range,
        ),
        "descriptor_scope": (
            "Computational descriptors only; they are not disease scores or "
            "biological severity labels."
        ),
    }


def build_combined_checks(
    *,
    baseline_report: dict[str, Any],
    conditions: list[dict[str, Any]],
    expected_condition_count: int,
) -> dict[str, dict[str, Any]]:
    """Build PASS/FAIL checks for the E2 batch report."""

    completed = [item for item in conditions if item.get("status") == "completed"]
    failed_count = len(conditions) - len(completed)
    control_equivalent = [
        item for item in conditions if item.get("baseline_equivalent") is True
    ]
    return {
        "baseline_simulation_passed": _check(True, baseline_report.get("overall_pass")),
        "condition_count": _check(expected_condition_count, len(conditions)),
        "all_conditions_completed": _check(0, failed_count),
        "completed_condition_count": _check(expected_condition_count, len(completed)),
        "all_completed_conditions_passed": _check(
            True,
            all(item.get("overall_pass") is True for item in completed),
        ),
        "control_equivalent_condition_present": _check(
            True,
            len(control_equivalent) == 1,
        ),
        "control_equivalent_condition_pass": _check(
            True,
            len(control_equivalent) == 1
            and all(
                item.get("status") == "completed"
                and item.get("baseline_equivalence", {}).get("pass") is True
                for item in control_equivalent
            ),
        ),
        "controlled_variables_preserved_for_completed_conditions": _check(
            True,
            all(
                item.get("controlled_variables", {}).get("match") is True
                for item in completed
            ),
        ),
        "fresh_simulation_state_per_condition_declared": _check(True, True),
    }


def _run_condition(
    *,
    baseline_config: HealthyBaselineConfig,
    baseline_report: dict[str, Any],
    sweep_config: CombinedPhenotypeSweepConfig,
    spec: CombinedPhenotypeConditionSpec,
    runner: ConditionRunner,
) -> dict[str, Any]:
    perturbation = spec.perturbation(experiment_id=sweep_config.experiment_id)
    base = spec.to_report(experiment_id=sweep_config.experiment_id)
    try:
        condition_report = runner(baseline_config, perturbation, spec.condition_id)
    except Exception as exc:
        return {
            **base,
            "status": "error",
            "overall_pass": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    condition_config = perturbation.apply_to_config(baseline_config)
    controlled = {
        "baseline": build_controlled_variables(baseline_config),
        "condition": build_controlled_variables(condition_config),
    }
    controlled["match"] = controlled["baseline"] == controlled["condition"]
    comparison = compare_locomotion_reports(baseline_report, condition_report)
    baseline_equivalence = (
        evaluate_identity_equivalence(baseline_report, condition_report)
        if spec.baseline_equivalent
        else None
    )
    checks = _condition_checks(
        baseline_report=baseline_report,
        condition_report=condition_report,
        perturbation_metadata=perturbation.metadata(),
        controlled_variables_match=controlled["match"],
        baseline_equivalence=baseline_equivalence,
        expected_step_count=baseline_config.expected_step_count(),
    )
    return {
        **base,
        "status": "completed",
        "controlled_variables": controlled,
        "report": condition_report,
        "comparison": comparison,
        "characterization": build_condition_characterization(comparison),
        "baseline_equivalence": baseline_equivalence,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
    }


def _condition_checks(
    *,
    baseline_report: dict[str, Any],
    condition_report: dict[str, Any],
    perturbation_metadata: dict[str, Any],
    controlled_variables_match: bool,
    baseline_equivalence: dict[str, Any] | None,
    expected_step_count: int,
) -> dict[str, dict[str, Any]]:
    metrics = condition_report.get("derived_locomotion_metrics", {})
    action_transform = condition_report.get("action_transformation_summary", {})
    action_structural = action_transform.get("structural_checks", {})
    controller_transform = condition_report.get("controller_transformation_summary", {})
    controller_structural = controller_transform.get("structural_checks", {})
    checks = {
        "baseline_simulation_passed": _check(True, baseline_report.get("overall_pass")),
        "condition_simulation_passed": _check(True, condition_report.get("overall_pass")),
        "controlled_variables_match": _check(True, controlled_variables_match),
        "perturbation_metadata_complete": _check(
            True, perturbation_metadata_complete(perturbation_metadata)
        ),
        "composite_perturbation_used": _check(
            "composite", perturbation_metadata.get("type")
        ),
        "observations_finite": _check(True, metrics.get("observations_are_finite")),
        "metrics_finite": _check(True, metrics.get("derived_metrics_are_finite")),
        "expected_step_count": _check(expected_step_count, metrics.get("step_count")),
        "action_dimensions_valid": _check(
            True, action_transform.get("action_dimensions_valid")
        ),
        "joint_angle_transform_matches_expected": _check(
            True,
            action_structural.get(
                "joint_angle_transform_matches_expected", {}
            ).get("observed"),
        ),
        "adhesion_commands_preserved": _check(
            True, action_transform.get("adhesion_commands_preserved")
        ),
        "controller_dimensions_valid": _check(
            True, controller_transform.get("controller_dimensions_valid")
        ),
        "cpg_coupling_transform_matches_expected": _check(
            True,
            controller_structural.get(
                "cpg_coupling_transform_matches_expected", {}
            ).get("observed"),
        ),
    }
    if baseline_equivalence is not None:
        checks["baseline_equivalence_pass"] = _check(
            True, baseline_equivalence.get("pass")
        )
    return checks


def _default_condition_runner(
    *, repo_root: str | Path | None
) -> ConditionRunner:
    def runner(
        config: HealthyBaselineConfig,
        perturbation: Perturbation | None,
        condition_id: str,
    ) -> dict[str, Any]:
        return run_locomotion(
            config,
            repo_root=repo_root,
            perturbation=perturbation,
            condition_id=condition_id,
            include_condition_metadata=True,
        )

    return runner


def _interaction_metric(
    *,
    combined: dict[str, Any],
    motor_only: dict[str, Any],
    coordination_only: dict[str, Any],
    metric: str,
) -> dict[str, Any]:
    combined_delta = _metric_delta(combined, metric)
    motor_delta = _metric_delta(motor_only, metric)
    coordination_delta = _metric_delta(coordination_only, metric)
    if combined_delta is None or motor_delta is None or coordination_delta is None:
        return {"status": "unavailable"}
    expected_additive_delta = motor_delta + coordination_delta
    residual = combined_delta - expected_additive_delta
    return {
        "status": "completed",
        "combined_delta": combined_delta,
        "motor_only_delta": motor_delta,
        "coordination_only_delta": coordination_delta,
        "expected_additive_delta": expected_additive_delta,
        "interaction_residual": residual,
        "residual_relative_to_expected": _residual_ratio(
            residual,
            expected_additive_delta,
        ),
        "interaction_category": _interaction_category(
            combined_delta,
            expected_additive_delta,
        ),
    }


def _interaction_category(combined_delta: float, expected_additive_delta: float) -> str:
    if abs(expected_additive_delta) <= 1e-12:
        return "residual_reported_no_categorical_claim"
    if combined_delta * expected_additive_delta < 0:
        return "direction_reversal"
    residual_ratio = abs(combined_delta - expected_additive_delta) / abs(
        expected_additive_delta
    )
    if residual_ratio <= INTERACTION_TOLERANCE:
        return "approximately_additive"
    if abs(combined_delta) < abs(expected_additive_delta):
        return "sub_additive"
    return "super_additive"


def _residual_ratio(residual: float, expected_additive_delta: float) -> float | None:
    if abs(expected_additive_delta) <= 1e-12:
        return None
    return residual / abs(expected_additive_delta)


def _metric_delta(condition: dict[str, Any], metric: str) -> float | None:
    scalar = condition.get("comparison", {}).get("scalars", {}).get(metric, {})
    return _finite_or_none(scalar.get("absolute_delta"))


def _comparison_has_metric(condition: dict[str, Any], metric: str) -> bool:
    return metric in condition.get("comparison", {}).get("scalars", {})


def _scalar(comparison: dict[str, Any], metric: str) -> dict[str, Any]:
    return comparison.get("scalars", {}).get(
        metric,
        {
            "baseline": None,
            "perturbed": None,
            "absolute_delta": None,
            "relative_delta": None,
        },
    )


def _relative_change_label(relative_delta: Any, *, tolerance: float = 0.05) -> str:
    value = _finite_or_none(relative_delta)
    if value is None:
        return "unavailable"
    if value <= -tolerance:
        return "decreased"
    if value >= tolerance:
        return "increased"
    return "minimal_change"


def _magnitude_label(
    relative_delta: Any,
    *,
    fallback_absolute_delta: Any = None,
    tolerance: float = 0.05,
) -> str:
    value = _finite_or_none(relative_delta)
    if value is None:
        value = _finite_or_none(fallback_absolute_delta)
    if value is None:
        return "unavailable"
    if abs(value) < tolerance:
        return "minimal_change"
    return "changed"


def _descriptive_class(
    *,
    displacement: dict[str, Any],
    speed: dict[str, Any],
    yaw: dict[str, Any],
    height_mean: dict[str, Any],
    height_range: dict[str, Any],
) -> str:
    locomotor = max(
        _abs_or_zero(displacement.get("relative_delta")),
        _abs_or_zero(speed.get("relative_delta")),
    )
    directional = _abs_or_zero(yaw.get("relative_delta"))
    if directional == 0:
        directional = min(_abs_or_zero(yaw.get("absolute_delta")), 1.0)
    postural = max(
        _abs_or_zero(height_mean.get("relative_delta")),
        _abs_or_zero(height_range.get("relative_delta")),
    )
    largest = max(locomotor, directional, postural)
    if largest < 0.05:
        return "low-magnitude effect"
    ordered = sorted(
        (
            ("motor-output", locomotor),
            ("directional", directional),
            ("postural", postural),
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    if ordered[0][1] >= 1.5 * max(ordered[1][1], 1e-12):
        if ordered[0][0] == "motor-output":
            return "predominantly motor-output effect"
        if ordered[0][0] == "directional":
            return "predominantly directional effect"
        return "mixed effect with prominent postural change"
    return "mixed effect"


def _source_api_findings() -> dict[str, Any]:
    return {
        "flygym_version_target": "2.1.0",
        "controller_stage_intervention": (
            "CPGCouplingScalePerturbation scales "
            "controller.cpg_network.coupling_weights after controller "
            "construction and before rollout."
        ),
        "action_stage_intervention": (
            "GlobalActionScalePerturbation scales LocomotionAction.joint_angles "
            "after each controller step and before apply_locomotion_action."
        ),
        "unchanged_by_e2": [
            "simulation duration",
            "simulation timestep",
            "world",
            "spawn",
            "fly construction parameters",
            "skeleton preset",
            "actuator architecture",
            "adhesion commands",
            "baseline controller intrinsic parameters",
        ],
    }


def _scale_key(motor_scale: float, coupling_scale: float) -> tuple[float, float]:
    return (round(float(motor_scale), 12), round(float(coupling_scale), 12))


def _require_name(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string.")
    return value.strip()


def _finite_nonnegative_float(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be finite and non-negative.")
    return result


def _finite_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _abs_or_zero(value: Any) -> float:
    result = _finite_or_none(value)
    return abs(result) if result is not None else 0.0


def _reject_condition_mapping_terms(value: str) -> None:
    lowered = value.lower()
    for term in ("dopamine", "neuron_loss", "pd_stage", "parkinson_severity"):
        if term in lowered:
            raise ValueError(
                f"Unsupported biological mapping term in E2 condition: {term}"
            )


def _check(expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


__all__ = [
    "CombinedPhenotypeConditionSpec",
    "CombinedPhenotypeSweepConfig",
    "LITERATURE_GROUNDING_SUMMARY",
    "PRIMARY_METRICS",
    "SCIENTIFIC_SCOPE",
    "build_combined_checks",
    "build_combined_phenotype_report",
    "build_combined_phenotype_unavailable_report",
    "build_condition_characterization",
    "build_interaction_analysis",
    "load_combined_phenotype_sweep_config",
    "run_combined_phenotype_sweep",
]
