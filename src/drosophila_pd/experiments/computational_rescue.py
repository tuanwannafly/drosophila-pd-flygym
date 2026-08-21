"""Preregistered computational rescue experiment for Milestone E5."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
import math
from pathlib import Path
from typing import Any, Callable

import yaml

from drosophila_pd.anatomy.audit import git_commit, runtime_environment
from drosophila_pd.experiments.candidate_robustness import (
    FROZEN_CANDIDATE_COUPLING_SCALE,
    FROZEN_CANDIDATE_MOTOR_SCALE,
    REQUIRED_E3_DURATION_S,
    REQUIRED_E3_SEEDS,
)
from drosophila_pd.experiments.healthy_baseline import (
    HealthyBaselineConfig,
    run_locomotion,
)
from drosophila_pd.experiments.perturbation_experiment import (
    build_controlled_variables,
)
from drosophila_pd.metrics.comparison import evaluate_identity_equivalence
from drosophila_pd.perturbations import (
    CPGCouplingScalePerturbation,
    CompositePerturbation,
    GlobalActionScalePerturbation,
    Perturbation,
    perturbation_metadata_complete,
)


CONTROL_MOTOR_SCALE = 1.0
CONTROL_COUPLING_SCALE = 1.0
MOTOR_PARTIAL_RESCUE_SCALE = 0.9
COUPLING_PARTIAL_RESCUE_SCALE = 0.875

REQUIRED_E5_CONDITION_MATRIX = (
    ("control", "control", CONTROL_MOTOR_SCALE, CONTROL_COUPLING_SCALE),
    (
        "impaired_candidate",
        "impaired_candidate",
        FROZEN_CANDIDATE_MOTOR_SCALE,
        FROZEN_CANDIDATE_COUPLING_SCALE,
    ),
    (
        "motor_partial_rescue",
        "partial_rescue",
        MOTOR_PARTIAL_RESCUE_SCALE,
        FROZEN_CANDIDATE_COUPLING_SCALE,
    ),
    (
        "coordination_partial_rescue",
        "partial_rescue",
        FROZEN_CANDIDATE_MOTOR_SCALE,
        COUPLING_PARTIAL_RESCUE_SCALE,
    ),
    (
        "combined_partial_rescue",
        "partial_rescue",
        MOTOR_PARTIAL_RESCUE_SCALE,
        COUPLING_PARTIAL_RESCUE_SCALE,
    ),
    (
        "full_computational_restoration_reference",
        "restoration_reference",
        CONTROL_MOTOR_SCALE,
        CONTROL_COUPLING_SCALE,
    ),
)

PRIMARY_ENDPOINTS = (
    "mean_planar_speed_mm_s",
    "planar_path_length_mm",
)

SECONDARY_ENDPOINTS = (
    "planar_displacement_mm",
    "trajectory_efficiency",
    "heading_yaw_abs_change_rad",
    "body_height_min_mm",
    "body_height_mean_mm",
    "body_height_range_mm",
    "joint_angle_action_abs_mean",
)

RECOVERY_CLASSIFICATIONS = {
    "DIRECTIONALLY_RESCUED",
    "MIXED",
    "NO_RESCUE",
    "UNSTABLE",
}

RESCUE_CONDITION_IDS = (
    "motor_partial_rescue",
    "coordination_partial_rescue",
    "combined_partial_rescue",
)

REFERENCE_CONDITION_ID = "full_computational_restoration_reference"
CONTROL_CONDITION_ID = "control"
IMPAIRED_CONDITION_ID = "impaired_candidate"

RECOVERY_EPSILON = 1e-9

SCIENTIFIC_SCOPE = (
    "Milestone E5 tests preregistered computational reversibility of the "
    "frozen E3/E4 phenomenological candidate. It is not an L-DOPA simulation, "
    "dopamine restoration, neuron restoration, pharmacological modeling, or "
    "biological rescue validation."
)

ConditionRunner = Callable[
    [HealthyBaselineConfig, Perturbation | None, str], dict[str, Any]
]


@dataclass(frozen=True)
class ComputationalRescueConditionSpec:
    """One preregistered E5 condition."""

    condition_id: str
    category: str
    motor_scale: float
    coupling_scale: float
    rescue_axis: str | None = None
    description: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ComputationalRescueConditionSpec":
        condition = cls(
            condition_id=_require_name(data, "condition_id"),
            category=_require_name(data, "category"),
            motor_scale=_finite_nonnegative_float(
                data.get("motor_scale"), "condition.motor_scale"
            ),
            coupling_scale=_finite_nonnegative_float(
                data.get("coupling_scale"), "condition.coupling_scale"
            ),
            rescue_axis=data.get("rescue_axis"),
            description=data.get("description"),
        )
        condition.validate()
        return condition

    def validate(self) -> None:
        if self.category not in {
            "control",
            "impaired_candidate",
            "partial_rescue",
            "restoration_reference",
        }:
            raise ValueError(f"Unsupported E5 condition category: {self.category}")
        if self.rescue_axis is not None and self.rescue_axis not in {
            "motor",
            "coordination",
            "combined",
            "reference",
        }:
            raise ValueError(f"Unsupported E5 rescue_axis: {self.rescue_axis}")

    @property
    def is_unperturbed_control(self) -> bool:
        return self.condition_id == CONTROL_CONDITION_ID

    @property
    def is_rescue_condition(self) -> bool:
        return self.condition_id in RESCUE_CONDITION_IDS

    @property
    def is_restoration_reference(self) -> bool:
        return self.condition_id == REFERENCE_CONDITION_ID

    def perturbation(self, *, experiment_id: str) -> CompositePerturbation | None:
        if self.is_unperturbed_control:
            return None
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
        perturbation = self.perturbation(experiment_id=experiment_id)
        return {
            "condition_id": self.condition_id,
            "category": self.category,
            "rescue_axis": self.rescue_axis,
            "motor_scale": self.motor_scale,
            "coupling_scale": self.coupling_scale,
            "description": self.description,
            "perturbation": (
                perturbation.metadata() if perturbation is not None else None
            ),
        }


@dataclass(frozen=True)
class ComputationalRescueConfig:
    """Validated Milestone E5 configuration."""

    experiment_id: str
    seeds: tuple[int, ...]
    duration_s: float
    conditions: tuple[ComputationalRescueConditionSpec, ...]
    frozen_states: dict[str, Any]
    midpoint_derivation: dict[str, Any]
    primary_endpoints: tuple[str, ...]
    secondary_endpoints: tuple[str, ...]
    recovery_metric: dict[str, Any]
    classification_policy: dict[str, Any]
    scientific_frame: dict[str, Any]
    validation_design: dict[str, Any]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ComputationalRescueConfig":
        validation_design = dict(data.get("validation_design") or {})
        raw_seeds = validation_design.get("seeds")
        raw_conditions = data.get("conditions")
        if not isinstance(raw_seeds, list) or not raw_seeds:
            raise ValueError("E5 validation_design.seeds must be a non-empty list.")
        if not isinstance(raw_conditions, list) or not raw_conditions:
            raise ValueError("E5 configuration requires explicit conditions.")
        config = cls(
            experiment_id=_require_name(data, "experiment_id"),
            seeds=tuple(
                _nonnegative_int(seed, "validation_design.seeds")
                for seed in raw_seeds
            ),
            duration_s=_positive_float(
                validation_design.get("duration_s"),
                "validation_design.duration_s",
            ),
            conditions=tuple(
                ComputationalRescueConditionSpec.from_mapping(item)
                for item in raw_conditions
            ),
            frozen_states=dict(data.get("frozen_states") or {}),
            midpoint_derivation=dict(data.get("midpoint_derivation") or {}),
            primary_endpoints=tuple(data.get("primary_endpoints") or ()),
            secondary_endpoints=tuple(data.get("secondary_endpoints") or ()),
            recovery_metric=dict(data.get("recovery_metric") or {}),
            classification_policy=dict(data.get("classification_policy") or {}),
            scientific_frame=dict(data.get("scientific_frame") or {}),
            validation_design=validation_design,
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.seeds != REQUIRED_E3_SEEDS:
            raise ValueError("Milestone E5 seed set must remain [0, 1, 2, 3, 4].")
        if not math.isclose(
            self.duration_s,
            REQUIRED_E3_DURATION_S,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("Milestone E5 duration_s must remain 1.0.")
        observed = tuple(
            (
                condition.condition_id,
                condition.category,
                condition.motor_scale,
                condition.coupling_scale,
            )
            for condition in self.conditions
        )
        if not _matrix_close(observed, REQUIRED_E5_CONDITION_MATRIX):
            raise ValueError(
                "Milestone E5 uses the fixed preregistered condition matrix; "
                "do not alter rescue values without explicit authorization."
            )
        if self.primary_endpoints != PRIMARY_ENDPOINTS:
            raise ValueError("Milestone E5 primary endpoints are preregistered.")
        for endpoint in self.secondary_endpoints:
            if endpoint != "adhesion_summary" and endpoint not in SECONDARY_ENDPOINTS:
                raise ValueError(f"Unsupported E5 secondary endpoint: {endpoint}")
        _validate_frozen_states(self.frozen_states)
        _validate_midpoint_derivation(self.midpoint_derivation)
        _validate_policy_flags(self)

    def condition_by_id(self, condition_id: str) -> ComputationalRescueConditionSpec:
        for condition in self.conditions:
            if condition.condition_id == condition_id:
                return condition
        raise KeyError(condition_id)

    def to_report(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "validation_design": {
                **self.validation_design,
                "duration_s": self.duration_s,
                "seeds": list(self.seeds),
            },
            "frozen_states": deepcopy(self.frozen_states),
            "midpoint_derivation": deepcopy(self.midpoint_derivation),
            "primary_endpoints": list(self.primary_endpoints),
            "secondary_endpoints": list(self.secondary_endpoints),
            "recovery_metric": deepcopy(self.recovery_metric),
            "classification_policy": deepcopy(self.classification_policy),
            "scientific_frame": deepcopy(self.scientific_frame),
            "conditions": [
                condition.to_report(experiment_id=self.experiment_id)
                for condition in self.conditions
            ],
            "condition_matrix_policy": "fixed_preregistered_rescue_matrix",
        }


def load_computational_rescue_config(path: str | Path) -> ComputationalRescueConfig:
    """Load a Milestone E5 YAML configuration file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("E5 configuration root must be a mapping.")
    return ComputationalRescueConfig.from_mapping(loaded)


def run_computational_rescue_validation(
    *,
    baseline_config: HealthyBaselineConfig,
    rescue_config: ComputationalRescueConfig,
    repo_root: str | Path | None = None,
    condition_runner: ConditionRunner | None = None,
) -> dict[str, Any]:
    """Run every preregistered E5 condition for every seed."""

    runner = condition_runner or _default_condition_runner(repo_root=repo_root)
    seed_runs = [
        _run_seed_conditions(
            baseline_config=baseline_config,
            rescue_config=rescue_config,
            seed=seed,
            runner=runner,
        )
        for seed in rescue_config.seeds
    ]
    return build_computational_rescue_report(
        baseline_config=baseline_config,
        rescue_config=rescue_config,
        seed_runs=seed_runs,
        repo_root=repo_root,
    )


def build_computational_rescue_report(
    *,
    baseline_config: HealthyBaselineConfig,
    rescue_config: ComputationalRescueConfig,
    seed_runs: list[dict[str, Any]],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the combined E5 report."""

    condition_assessments = build_condition_assessments(
        seed_runs=seed_runs,
        rescue_config=rescue_config,
    )
    full_reference_equivalence = build_full_restoration_reference_equivalence(
        seed_runs
    )
    checks = build_computational_rescue_checks(
        seed_runs=seed_runs,
        rescue_config=rescue_config,
        condition_assessments=condition_assessments,
        full_reference_equivalence=full_reference_equivalence,
    )
    return {
        "experiment_id": rescue_config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "baseline_config": baseline_config.to_report(),
        "validation_config": rescue_config.to_report(),
        "preregistered_design": _preregistered_design_summary(rescue_config),
        "paired_execution": {
            "seeds": list(rescue_config.seeds),
            "duration_s": rescue_config.duration_s,
            "condition_count_per_seed": len(rescue_config.conditions),
            "fresh_fly_world_simulation_per_condition": True,
            "raw_trajectories_stored_in_report": False,
            "gpu_or_rendering_required": False,
        },
        "seed_runs": seed_runs,
        "condition_assessments": condition_assessments,
        "full_restoration_reference_equivalence": full_reference_equivalence,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_computational_rescue_unavailable_report(
    error: BaseException,
    *,
    baseline_config: HealthyBaselineConfig,
    rescue_config: ComputationalRescueConfig,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a report for environments where E5 cannot execute."""

    return {
        "experiment_id": rescue_config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "baseline_config": baseline_config.to_report(),
        "validation_config": rescue_config.to_report(),
        "seed_runs": [],
        "condition_assessments": {},
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_recovery_fraction(
    *,
    control: Any,
    impaired: Any,
    rescue: Any,
    epsilon: float = RECOVERY_EPSILON,
) -> dict[str, Any]:
    """Compute baseline-normalized computational recovery fraction."""

    control_value = _finite_or_none(control)
    impaired_value = _finite_or_none(impaired)
    rescue_value = _finite_or_none(rescue)
    if control_value is None or impaired_value is None or rescue_value is None:
        return {
            "control": control_value,
            "impaired": impaired_value,
            "rescue": rescue_value,
            "denominator": None,
            "denominator_near_zero": None,
            "recovery_fraction": None,
            "direction_toward_control": None,
            "no_farther_from_control": None,
        }
    denominator = control_value - impaired_value
    denominator_near_zero = abs(denominator) <= epsilon
    if denominator_near_zero:
        recovery_fraction = None
        direction_toward_control = None
    else:
        recovery_fraction = (rescue_value - impaired_value) / denominator
        direction_toward_control = recovery_fraction > 0
    no_farther = (
        abs(rescue_value - control_value)
        <= abs(impaired_value - control_value) + epsilon
    )
    return {
        "control": control_value,
        "impaired": impaired_value,
        "rescue": rescue_value,
        "denominator": denominator,
        "denominator_near_zero": denominator_near_zero,
        "recovery_fraction": recovery_fraction,
        "direction_toward_control": direction_toward_control,
        "no_farther_from_control": no_farther,
    }


def build_condition_assessments(
    *,
    seed_runs: list[dict[str, Any]],
    rescue_config: ComputationalRescueConfig,
) -> dict[str, Any]:
    """Aggregate recovery fractions and classifications by condition."""

    assessments = {}
    for condition_id in (*RESCUE_CONDITION_IDS, REFERENCE_CONDITION_ID):
        spec = rescue_config.condition_by_id(condition_id)
        entries = []
        for seed_run in seed_runs:
            condition = _seed_condition(seed_run, condition_id)
            entries.append(
                {
                    "seed": seed_run.get("seed"),
                    "status": condition.get("status") if condition else "missing",
                    "overall_pass": condition.get("overall_pass") if condition else False,
                    "recovery": condition.get("recovery") if condition else {},
                }
            )
        primary_aggregate = {
            metric: _aggregate_metric_recovery(entries, metric)
            for metric in PRIMARY_ENDPOINTS
        }
        secondary_aggregate = {
            metric: _aggregate_metric_recovery(entries, metric)
            for metric in SECONDARY_ENDPOINTS
        }
        classification = (
            None
            if spec.is_restoration_reference
            else classify_rescue_condition(
                entries=entries,
                primary_aggregate=primary_aggregate,
                expected_seed_count=len(rescue_config.seeds),
            )
        )
        assessments[condition_id] = {
            "condition_id": condition_id,
            "category": spec.category,
            "rescue_axis": spec.rescue_axis,
            "motor_scale": spec.motor_scale,
            "coupling_scale": spec.coupling_scale,
            "classification": classification,
            "classification_scope": (
                "Computational direction only; not biological rescue."
                if classification is not None
                else "Software/control-equivalence reference; not a rescue label."
            ),
            "primary_endpoints": primary_aggregate,
            "secondary_endpoints": secondary_aggregate,
            "per_seed": entries,
        }
    return assessments


def classify_rescue_condition(
    *,
    entries: list[dict[str, Any]],
    primary_aggregate: dict[str, Any],
    expected_seed_count: int,
) -> str:
    """Classify an E5 partial-rescue condition."""

    stable = (
        len(entries) == expected_seed_count
        and all(entry.get("status") == "completed" for entry in entries)
        and all(entry.get("overall_pass") is True for entry in entries)
    )
    if not stable:
        return "UNSTABLE"

    aggregate_improved = [
        summary.get("aggregate_direction_toward_control") is True
        for summary in primary_aggregate.values()
    ]
    aggregate_no_farther = [
        summary.get("aggregate_no_farther_from_control") is True
        for summary in primary_aggregate.values()
    ]
    per_seed_consistent = [
        summary.get("per_seed_direction_toward_control_count")
        == summary.get("count")
        for summary in primary_aggregate.values()
    ]
    improved_count = sum(1 for value in aggregate_improved if value)
    if (
        improved_count == len(PRIMARY_ENDPOINTS)
        and all(aggregate_no_farther)
        and all(per_seed_consistent)
    ):
        return "DIRECTIONALLY_RESCUED"
    if improved_count > 0:
        return "MIXED"
    return "NO_RESCUE"


def build_full_restoration_reference_equivalence(
    seed_runs: list[dict[str, Any]]
) -> dict[str, Any]:
    """Summarize control-vs-reference deterministic equivalence."""

    per_seed = []
    for seed_run in seed_runs:
        equivalence = seed_run.get("full_restoration_reference_equivalence")
        per_seed.append(
            {
                "seed": seed_run.get("seed"),
                "pass": (
                    equivalence.get("pass")
                    if isinstance(equivalence, dict)
                    else False
                ),
                "equivalence": equivalence,
            }
        )
    return {
        "condition_id": REFERENCE_CONDITION_ID,
        "definition": (
            "The 1.0/1.0 restoration reference must reproduce the unperturbed "
            "control condition within existing deterministic tolerances."
        ),
        "pass": bool(per_seed) and all(item["pass"] is True for item in per_seed),
        "per_seed": per_seed,
        "terminology_boundary": (
            "This is not full rescue, cure, L-DOPA rescue, or dopamine restoration."
        ),
    }


def build_computational_rescue_checks(
    *,
    seed_runs: list[dict[str, Any]],
    rescue_config: ComputationalRescueConfig,
    condition_assessments: dict[str, Any],
    full_reference_equivalence: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build software/simulation PASS checks for E5."""

    expected_conditions = len(rescue_config.seeds) * len(rescue_config.conditions)
    completed_conditions = [
        condition
        for seed_run in seed_runs
        for condition in seed_run.get("conditions", [])
        if condition.get("status") == "completed"
    ]
    all_conditions = [
        condition
        for seed_run in seed_runs
        for condition in seed_run.get("conditions", [])
    ]
    return {
        "seed_count": _check(len(rescue_config.seeds), len(seed_runs)),
        "condition_count": _check(expected_conditions, len(all_conditions)),
        "all_conditions_completed": _check(
            expected_conditions, len(completed_conditions)
        ),
        "all_completed_conditions_passed": _check(
            True,
            all(condition.get("overall_pass") is True for condition in completed_conditions),
        ),
        "controlled_variables_preserved": _check(
            True,
            all(
                condition.get("controlled_variables", {}).get("match") is True
                for condition in completed_conditions
            ),
        ),
        "primary_endpoints_present": _check(
            True,
            all(
                all(metric in condition.get("metrics", {}) for metric in PRIMARY_ENDPOINTS)
                for condition in completed_conditions
            ),
        ),
        "recovery_reports_produced": _check(
            True,
            all(condition_id in condition_assessments for condition_id in RESCUE_CONDITION_IDS),
        ),
        "rescue_classifications_allowed": _check(
            True,
            all(
                condition_assessments[condition_id]["classification"]
                in RECOVERY_CLASSIFICATIONS
                for condition_id in RESCUE_CONDITION_IDS
            ),
        ),
        "full_restoration_reference_equivalence": _check(
            True, full_reference_equivalence.get("pass")
        ),
        "no_arbitrary_recovery_threshold": _check(
            True,
            rescue_config.classification_policy.get(
                "no_arbitrary_recovery_thresholds"
            ),
        ),
        "biological_rescue_claim_forbidden": _check(
            False,
            rescue_config.classification_policy.get(
                "biological_rescue_claim_permitted"
            ),
        ),
        "post_hoc_tuning_forbidden": _check(
            False, rescue_config.frozen_states.get("post_hoc_tuning_permitted")
        ),
    }


def _run_seed_conditions(
    *,
    baseline_config: HealthyBaselineConfig,
    rescue_config: ComputationalRescueConfig,
    seed: int,
    runner: ConditionRunner,
) -> dict[str, Any]:
    seed_config = _config_with_seed_and_duration(
        baseline_config,
        seed=seed,
        duration_s=rescue_config.duration_s,
    )
    control_variables = build_controlled_variables(seed_config)
    condition_results = []
    for spec in rescue_config.conditions:
        condition_results.append(
            _run_condition(
                seed_config=seed_config,
                rescue_config=rescue_config,
                spec=spec,
                control_variables=control_variables,
                runner=runner,
            )
        )
    by_id = {condition["condition_id"]: condition for condition in condition_results}
    _attach_seed_recovery(by_id)
    full_reference_equivalence = _seed_full_reference_equivalence(by_id)
    checks = _seed_checks(condition_results, full_reference_equivalence)
    all_completed = all(
        condition.get("status") == "completed" for condition in condition_results
    )
    return {
        "seed": seed,
        "status": "completed" if all_completed else "error",
        "duration_s": rescue_config.duration_s,
        "condition_ids": [condition.condition_id for condition in rescue_config.conditions],
        "conditions": condition_results,
        "full_restoration_reference_equivalence": full_reference_equivalence,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
    }


def _run_condition(
    *,
    seed_config: HealthyBaselineConfig,
    rescue_config: ComputationalRescueConfig,
    spec: ComputationalRescueConditionSpec,
    control_variables: dict[str, Any],
    runner: ConditionRunner,
) -> dict[str, Any]:
    perturbation = spec.perturbation(experiment_id=rescue_config.experiment_id)
    condition_id = f"seed_{seed_config.random_seed}_{spec.condition_id}"
    condition_config = (
        perturbation.apply_to_config(seed_config)
        if perturbation is not None
        else seed_config
    )
    controlled = {
        "control": control_variables,
        "condition": build_controlled_variables(condition_config),
    }
    controlled["match"] = controlled["control"] == controlled["condition"]

    try:
        report = runner(seed_config, perturbation, condition_id)
    except Exception as exc:
        return {
            **spec.to_report(experiment_id=rescue_config.experiment_id),
            "seed": seed_config.random_seed,
            "status": "error",
            "overall_pass": False,
            "controlled_variables": controlled,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    metrics = extract_e5_metric_values(report)
    checks = _condition_checks(
        report=report,
        spec=spec,
        perturbation=perturbation,
        controlled_variables_match=controlled["match"],
        expected_step_count=seed_config.expected_step_count(),
    )
    return {
        **spec.to_report(experiment_id=rescue_config.experiment_id),
        "seed": seed_config.random_seed,
        "status": "completed",
        "controlled_variables": controlled,
        "report": report,
        "metrics": metrics,
        "adhesion": report.get("derived_locomotion_metrics", {})
        .get("controller_action_summary", {})
        .get("adhesion"),
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
    }


def extract_e5_metric_values(report: dict[str, Any]) -> dict[str, Any]:
    """Extract E5 scalar endpoints from one locomotion report."""

    metrics = report.get("derived_locomotion_metrics", {})
    height = metrics.get("body_height_mm", {})
    action = metrics.get("controller_action_summary", {})
    joint_abs = action.get("joint_angle_action_abs", {})
    yaw = _finite_or_none(metrics.get("heading_yaw_change_rad"))
    height_min = _finite_or_none(height.get("min"))
    height_max = _finite_or_none(height.get("max"))
    return {
        "mean_planar_speed_mm_s": _finite_or_none(
            metrics.get("mean_planar_speed_mm_s")
        ),
        "planar_path_length_mm": _finite_or_none(
            metrics.get("planar_path_length_mm")
        ),
        "planar_displacement_mm": _finite_or_none(
            metrics.get("planar_displacement_mm")
        ),
        "trajectory_efficiency": _finite_or_none(
            metrics.get("trajectory_efficiency")
        ),
        "heading_yaw_abs_change_rad": abs(yaw) if yaw is not None else None,
        "body_height_min_mm": height_min,
        "body_height_mean_mm": _finite_or_none(height.get("mean")),
        "body_height_range_mm": (
            height_max - height_min
            if height_max is not None and height_min is not None
            else None
        ),
        "joint_angle_action_abs_mean": _finite_or_none(joint_abs.get("mean")),
    }


def _attach_seed_recovery(by_id: dict[str, dict[str, Any]]) -> None:
    control = by_id.get(CONTROL_CONDITION_ID)
    impaired = by_id.get(IMPAIRED_CONDITION_ID)
    if not _condition_completed(control) or not _condition_completed(impaired):
        return
    for condition_id in (*RESCUE_CONDITION_IDS, REFERENCE_CONDITION_ID):
        condition = by_id.get(condition_id)
        if not _condition_completed(condition):
            continue
        condition["recovery"] = {
            metric: build_recovery_fraction(
                control=control["metrics"].get(metric),
                impaired=impaired["metrics"].get(metric),
                rescue=condition["metrics"].get(metric),
            )
            for metric in (*PRIMARY_ENDPOINTS, *SECONDARY_ENDPOINTS)
        }


def _seed_full_reference_equivalence(
    by_id: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    control = by_id.get(CONTROL_CONDITION_ID)
    reference = by_id.get(REFERENCE_CONDITION_ID)
    if not _condition_completed(control) or not _condition_completed(reference):
        return {
            "pass": False,
            "reason": "control or full restoration reference condition did not complete",
        }
    return evaluate_identity_equivalence(control["report"], reference["report"])


def _seed_checks(
    conditions: list[dict[str, Any]],
    full_reference_equivalence: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    completed = [condition for condition in conditions if condition.get("status") == "completed"]
    return {
        "all_conditions_completed": _check(len(conditions), len(completed)),
        "all_completed_conditions_passed": _check(
            True,
            all(condition.get("overall_pass") is True for condition in completed),
        ),
        "controlled_variables_match": _check(
            True,
            all(
                condition.get("controlled_variables", {}).get("match") is True
                for condition in completed
            ),
        ),
        "full_restoration_reference_equivalence": _check(
            True, full_reference_equivalence.get("pass")
        ),
    }


def _condition_checks(
    *,
    report: dict[str, Any],
    spec: ComputationalRescueConditionSpec,
    perturbation: Perturbation | None,
    controlled_variables_match: bool,
    expected_step_count: int,
) -> dict[str, dict[str, Any]]:
    metrics = report.get("derived_locomotion_metrics", {})
    checks = {
        "simulation_passed": _check(True, report.get("overall_pass")),
        "controlled_variables_match": _check(True, controlled_variables_match),
        "observations_finite": _check(True, metrics.get("observations_are_finite")),
        "metrics_finite": _check(True, metrics.get("derived_metrics_are_finite")),
        "expected_step_count": _check(expected_step_count, metrics.get("step_count")),
        "primary_endpoints_present": _check(
            True,
            all(
                extract_e5_metric_values(report).get(endpoint) is not None
                for endpoint in PRIMARY_ENDPOINTS
            ),
        ),
    }
    if perturbation is None:
        checks["unperturbed_control_condition"] = _check(
            CONTROL_CONDITION_ID, spec.condition_id
        )
        return checks

    metadata = perturbation.metadata()
    action_transform = report.get("action_transformation_summary", {})
    action_structural = action_transform.get("structural_checks", {})
    controller_transform = report.get("controller_transformation_summary", {})
    controller_structural = controller_transform.get("structural_checks", {})
    checks.update(
        {
            "perturbation_metadata_complete": _check(
                True, perturbation_metadata_complete(metadata)
            ),
            "composite_perturbation_used": _check("composite", metadata.get("type")),
            "effective_motor_scale": _check(
                spec.motor_scale,
                action_transform.get("effective_joint_angle_scale"),
            ),
            "effective_coupling_scale": _check(
                spec.coupling_scale,
                controller_transform.get("effective_cpg_coupling_scale"),
            ),
            "action_dimensions_valid": _check(
                True, action_transform.get("action_dimensions_valid")
            ),
            "adhesion_commands_preserved": _check(
                True, action_transform.get("adhesion_commands_preserved")
            ),
            "joint_angle_transform_matches_expected": _check(
                True,
                action_structural.get(
                    "joint_angle_transform_matches_expected", {}
                ).get("observed"),
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
    )
    return checks


def _aggregate_metric_recovery(
    entries: list[dict[str, Any]], metric: str
) -> dict[str, Any]:
    recoveries = []
    control_values = []
    impaired_values = []
    rescue_values = []
    direction_count = 0
    no_farther_count = 0
    denominator_near_zero_count = 0
    for entry in entries:
        recovery = (entry.get("recovery") or {}).get(metric, {})
        recoveries.append(_finite_or_none(recovery.get("recovery_fraction")))
        control_values.append(_finite_or_none(recovery.get("control")))
        impaired_values.append(_finite_or_none(recovery.get("impaired")))
        rescue_values.append(_finite_or_none(recovery.get("rescue")))
        if recovery.get("direction_toward_control") is True:
            direction_count += 1
        if recovery.get("no_farther_from_control") is True:
            no_farther_count += 1
        if recovery.get("denominator_near_zero") is True:
            denominator_near_zero_count += 1

    control_stats = _stats(control_values)
    impaired_stats = _stats(impaired_values)
    rescue_stats = _stats(rescue_values)
    recovery_stats = _stats(recoveries, allow_missing=True)
    aggregate_recovery = build_recovery_fraction(
        control=control_stats["mean"],
        impaired=impaired_stats["mean"],
        rescue=rescue_stats["mean"],
    )
    return {
        "count": len([value for value in rescue_values if value is not None]),
        "control": control_stats,
        "impaired": impaired_stats,
        "rescue": rescue_stats,
        "recovery_fraction": recovery_stats,
        "aggregate_recovery_fraction": aggregate_recovery.get("recovery_fraction"),
        "aggregate_direction_toward_control": aggregate_recovery.get(
            "direction_toward_control"
        ),
        "aggregate_no_farther_from_control": aggregate_recovery.get(
            "no_farther_from_control"
        ),
        "per_seed_direction_toward_control_count": direction_count,
        "per_seed_no_farther_from_control_count": no_farther_count,
        "denominator_near_zero_count": denominator_near_zero_count,
    }


def _preregistered_design_summary(
    rescue_config: ComputationalRescueConfig,
) -> dict[str, Any]:
    return {
        "control": {
            "motor_scale": CONTROL_MOTOR_SCALE,
            "coupling_scale": CONTROL_COUPLING_SCALE,
        },
        "frozen_impaired_candidate": {
            "motor_scale": FROZEN_CANDIDATE_MOTOR_SCALE,
            "coupling_scale": FROZEN_CANDIDATE_COUPLING_SCALE,
        },
        "midpoint_derivation": deepcopy(rescue_config.midpoint_derivation),
        "primary_endpoints": list(PRIMARY_ENDPOINTS),
        "secondary_endpoints": list(SECONDARY_ENDPOINTS),
        "rescue_condition_ids": list(RESCUE_CONDITION_IDS),
        "full_restoration_reference_condition_id": REFERENCE_CONDITION_ID,
        "no_parameter_sweep": True,
        "no_post_hoc_tuning": True,
        "not_biological_rescue": True,
    }


def _config_with_seed_and_duration(
    baseline_config: HealthyBaselineConfig,
    *,
    seed: int,
    duration_s: float,
) -> HealthyBaselineConfig:
    data = deepcopy(baseline_config.to_report())
    data["random_seed"] = int(seed)
    data.setdefault("simulation", {})["duration_s"] = float(duration_s)
    data["experiment_id"] = f"{baseline_config.experiment_id}_e5_seed_{seed}"
    return HealthyBaselineConfig.from_mapping(data)


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


def _condition_completed(condition: dict[str, Any] | None) -> bool:
    return condition is not None and condition.get("status") == "completed"


def _seed_condition(
    seed_run: dict[str, Any], condition_id: str
) -> dict[str, Any] | None:
    for condition in seed_run.get("conditions", []):
        if condition.get("condition_id") == condition_id:
            return condition
    return None


def _validate_frozen_states(frozen_states: dict[str, Any]) -> None:
    control = dict(frozen_states.get("control") or {})
    impaired = dict(frozen_states.get("impaired_candidate") or {})
    if not _close(control.get("motor_scale"), CONTROL_MOTOR_SCALE) or not _close(
        control.get("coupling_scale"), CONTROL_COUPLING_SCALE
    ):
        raise ValueError("E5 control state must remain 1.0 / 1.0.")
    if not _close(
        impaired.get("motor_scale"), FROZEN_CANDIDATE_MOTOR_SCALE
    ) or not _close(
        impaired.get("coupling_scale"), FROZEN_CANDIDATE_COUPLING_SCALE
    ):
        raise ValueError("E5 impaired candidate must remain 0.8 / 0.75.")
    if frozen_states.get("selected_before_execution") is not True:
        raise ValueError("E5 states must be selected before execution.")
    if frozen_states.get("post_hoc_tuning_permitted") is not False:
        raise ValueError("Post-hoc tuning is not permitted in E5.")


def _validate_midpoint_derivation(midpoint: dict[str, Any]) -> None:
    motor = dict(midpoint.get("motor_partial_rescue") or {})
    coupling = dict(midpoint.get("coupling_partial_rescue") or {})
    if not _close(motor.get("midpoint_value"), MOTOR_PARTIAL_RESCUE_SCALE):
        raise ValueError("E5 motor partial rescue midpoint must remain 0.9.")
    if not _close(coupling.get("midpoint_value"), COUPLING_PARTIAL_RESCUE_SCALE):
        raise ValueError("E5 coupling partial rescue midpoint must remain 0.875.")
    if not _close(
        (float(motor.get("impaired_value")) + float(motor.get("control_value"))) / 2,
        MOTOR_PARTIAL_RESCUE_SCALE,
    ):
        raise ValueError("E5 motor midpoint derivation is invalid.")
    if not _close(
        (
            float(coupling.get("impaired_value"))
            + float(coupling.get("control_value"))
        )
        / 2,
        COUPLING_PARTIAL_RESCUE_SCALE,
    ):
        raise ValueError("E5 coupling midpoint derivation is invalid.")
    if midpoint.get("derivation_selected_before_execution") is not True:
        raise ValueError("E5 midpoint derivation must be selected before execution.")
    if midpoint.get("alternative_rescue_values_permitted") is not False:
        raise ValueError("Alternative E5 rescue values are not permitted.")


def _validate_policy_flags(config: ComputationalRescueConfig) -> None:
    recovery = config.recovery_metric
    classification = config.classification_policy
    if recovery.get("biological_percentage_claim_permitted") is not False:
        raise ValueError("E5 recovery fraction must not be a biological percentage.")
    if set(classification.get("allowed_labels") or []) != RECOVERY_CLASSIFICATIONS:
        raise ValueError("E5 classification labels are fixed.")
    if classification.get("no_arbitrary_recovery_thresholds") is not True:
        raise ValueError("E5 must not define arbitrary recovery thresholds.")
    if classification.get("biological_rescue_claim_permitted") is not False:
        raise ValueError("E5 must not claim biological rescue.")


def _matrix_close(
    observed: tuple[tuple[str, str, float, float], ...],
    expected: tuple[tuple[str, str, float, float], ...],
) -> bool:
    if len(observed) != len(expected):
        return False
    for left, right in zip(observed, expected):
        if left[:2] != right[:2]:
            return False
        if not _close(left[2], right[2]) or not _close(left[3], right[3]):
            return False
    return True


def _stats(values: list[float | None], *, allow_missing: bool = False) -> dict[str, Any]:
    finite = [float(value) for value in values if value is not None and math.isfinite(value)]
    if not finite or (len(finite) != len(values) and not allow_missing):
        return {
            "count": len(finite),
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
            "median": None,
        }
    sorted_values = sorted(finite)
    mean = sum(finite) / len(finite)
    variance = sum((value - mean) ** 2 for value in finite) / len(finite)
    return {
        "count": len(finite),
        "mean": mean,
        "std": math.sqrt(variance),
        "min": min(finite),
        "max": max(finite),
        "median": _median(sorted_values),
    }


def _median(sorted_values: list[float]) -> float:
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2 == 1:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2


def _close(left: Any, right: Any) -> bool:
    try:
        return math.isclose(float(left), float(right), rel_tol=0.0, abs_tol=1e-12)
    except (TypeError, ValueError):
        return False


def _finite_nonnegative_float(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be finite and non-negative.")
    return result


def _positive_float(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be finite and positive.")
    return result


def _nonnegative_int(value: Any, name: str) -> int:
    result = int(value)
    if result < 0:
        raise ValueError(f"{name} must contain non-negative integers.")
    return result


def _finite_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _require_name(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string.")
    return value.strip()


def _check(expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


__all__ = [
    "COUPLING_PARTIAL_RESCUE_SCALE",
    "CONTROL_COUPLING_SCALE",
    "CONTROL_MOTOR_SCALE",
    "ComputationalRescueConditionSpec",
    "ComputationalRescueConfig",
    "MOTOR_PARTIAL_RESCUE_SCALE",
    "PRIMARY_ENDPOINTS",
    "RECOVERY_CLASSIFICATIONS",
    "REQUIRED_E5_CONDITION_MATRIX",
    "RESCUE_CONDITION_IDS",
    "SCIENTIFIC_SCOPE",
    "SECONDARY_ENDPOINTS",
    "build_computational_rescue_checks",
    "build_computational_rescue_report",
    "build_computational_rescue_unavailable_report",
    "build_condition_assessments",
    "build_full_restoration_reference_equivalence",
    "build_recovery_fraction",
    "classify_rescue_condition",
    "extract_e5_metric_values",
    "load_computational_rescue_config",
    "run_computational_rescue_validation",
]
