"""Multi-seed robustness validation for the frozen E3 candidate."""

from __future__ import annotations

from copy import deepcopy
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
from drosophila_pd.metrics.comparison import compare_locomotion_reports
from drosophila_pd.perturbations import (
    CPGCouplingScalePerturbation,
    CompositePerturbation,
    GlobalActionScalePerturbation,
    Perturbation,
    perturbation_metadata_complete,
)


FROZEN_CANDIDATE_MOTOR_SCALE = 0.8
FROZEN_CANDIDATE_COUPLING_SCALE = 0.75
REQUIRED_E3_SEEDS = (0, 1, 2, 3, 4)
REQUIRED_E3_DURATION_S = 1.0

SCIENTIFIC_SCOPE = (
    "Milestone E3 validates robustness of a phenomenological computational "
    "locomotor-deficit candidate across simulation seeds. It does not establish "
    "a mechanistic or biologically validated Parkinson's disease model."
)

KEY_METRICS = (
    "planar_displacement_mm",
    "mean_planar_speed_mm_s",
    "heading_yaw_change_rad",
    "heading_yaw_abs_change_rad",
    "trajectory_efficiency",
    "planar_path_length_mm",
    "body_height_min_mm",
    "body_height_mean_mm",
    "body_height_range_mm",
    "joint_angle_action_abs_mean",
)

ConditionRunner = Callable[
    [HealthyBaselineConfig, Perturbation | None, str], dict[str, Any]
]


@dataclass(frozen=True)
class E3CandidateDefinition:
    """Frozen computational candidate selected before E3 execution."""

    motor_scale: float
    coupling_scale: float
    preregistered_parameter_source: str
    selected_before_e3_execution: bool
    post_hoc_tuning_permitted: bool
    description: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "E3CandidateDefinition":
        candidate = cls(
            motor_scale=_finite_nonnegative_float(
                data.get("motor_scale"), "candidate.motor_scale"
            ),
            coupling_scale=_finite_nonnegative_float(
                data.get("coupling_scale"), "candidate.coupling_scale"
            ),
            preregistered_parameter_source=_require_name(
                data, "preregistered_parameter_source"
            ),
            selected_before_e3_execution=bool(
                data.get("selected_before_e3_execution")
            ),
            post_hoc_tuning_permitted=bool(data.get("post_hoc_tuning_permitted")),
            description=data.get("description"),
        )
        candidate.validate()
        return candidate

    def validate(self) -> None:
        if not math.isclose(
            self.motor_scale,
            FROZEN_CANDIDATE_MOTOR_SCALE,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("E3 candidate motor_scale must remain frozen at 0.8.")
        if not math.isclose(
            self.coupling_scale,
            FROZEN_CANDIDATE_COUPLING_SCALE,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("E3 candidate coupling_scale must remain frozen at 0.75.")
        if "Milestone E2" not in self.preregistered_parameter_source:
            raise ValueError("E3 candidate must record Milestone E2 as parameter source.")
        if self.selected_before_e3_execution is not True:
            raise ValueError("E3 candidate must be selected before E3 execution.")
        if self.post_hoc_tuning_permitted is not False:
            raise ValueError("Post-hoc tuning is not permitted inside E3.")

    def perturbation(self, *, experiment_id: str) -> CompositePerturbation:
        return CompositePerturbation(
            name="e3_frozen_candidate_motor_080_coupling_075",
            config_id=experiment_id,
            components=(
                CPGCouplingScalePerturbation(
                    scale=self.coupling_scale,
                    name="e3_candidate_coordination_proxy",
                    config_id=experiment_id,
                ),
                GlobalActionScalePerturbation(
                    scale=self.motor_scale,
                    name="e3_candidate_motor_vigor_proxy",
                    config_id=experiment_id,
                ),
            ),
        )

    def to_report(self, *, experiment_id: str) -> dict[str, Any]:
        return {
            "motor_scale": self.motor_scale,
            "coupling_scale": self.coupling_scale,
            "preregistered_parameter_source": self.preregistered_parameter_source,
            "selected_before_e3_execution": self.selected_before_e3_execution,
            "post_hoc_tuning_permitted": self.post_hoc_tuning_permitted,
            "description": self.description,
            "status": "frozen_before_e3_execution",
            "perturbation": self.perturbation(experiment_id=experiment_id).metadata(),
        }


@dataclass(frozen=True)
class CandidateRobustnessConfig:
    """Validated Milestone E3 validation configuration."""

    experiment_id: str
    seeds: tuple[int, ...]
    duration_s: float
    candidate: E3CandidateDefinition
    validation_design: dict[str, Any]
    scientific_frame: dict[str, Any]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "CandidateRobustnessConfig":
        validation_design = dict(data.get("validation_design") or {})
        raw_seeds = validation_design.get("seeds")
        if not isinstance(raw_seeds, list) or not raw_seeds:
            raise ValueError("E3 validation_design.seeds must be a non-empty list.")
        config = cls(
            experiment_id=_require_name(data, "experiment_id"),
            seeds=tuple(_nonnegative_int(seed, "validation_design.seeds") for seed in raw_seeds),
            duration_s=_positive_float(
                validation_design.get("duration_s"), "validation_design.duration_s"
            ),
            candidate=E3CandidateDefinition.from_mapping(
                dict(data.get("candidate") or {})
            ),
            validation_design=validation_design,
            scientific_frame=dict(data.get("scientific_frame") or {}),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.seeds != REQUIRED_E3_SEEDS:
            raise ValueError("Milestone E3 seed set must remain [0, 1, 2, 3, 4].")
        if not math.isclose(
            self.duration_s,
            REQUIRED_E3_DURATION_S,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("Milestone E3 duration_s must remain 1.0.")

    def to_report(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "validation_design": {
                **self.validation_design,
                "duration_s": self.duration_s,
                "seeds": list(self.seeds),
            },
            "candidate": self.candidate.to_report(experiment_id=self.experiment_id),
            "scientific_frame": self.scientific_frame,
        }


def load_candidate_robustness_config(path: str | Path) -> CandidateRobustnessConfig:
    """Load a Milestone E3 YAML configuration file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("E3 validation configuration root must be a mapping.")
    return CandidateRobustnessConfig.from_mapping(loaded)


def run_candidate_robustness_validation(
    *,
    baseline_config: HealthyBaselineConfig,
    validation_config: CandidateRobustnessConfig,
    repo_root: str | Path | None = None,
    condition_runner: ConditionRunner | None = None,
) -> dict[str, Any]:
    """Run all paired E3 seed conditions in one process."""

    runner = condition_runner or _default_condition_runner(repo_root=repo_root)
    pairs = [
        _run_seed_pair(
            baseline_config=baseline_config,
            validation_config=validation_config,
            seed=seed,
            runner=runner,
        )
        for seed in validation_config.seeds
    ]
    return build_candidate_robustness_report(
        baseline_config=baseline_config,
        validation_config=validation_config,
        pairs=pairs,
        repo_root=repo_root,
    )


def build_candidate_robustness_report(
    *,
    baseline_config: HealthyBaselineConfig,
    validation_config: CandidateRobustnessConfig,
    pairs: list[dict[str, Any]],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the combined E3 robustness report."""

    aggregate_statistics = build_aggregate_statistics(pairs)
    sign_consistency = build_sign_consistency(pairs)
    robustness_assessment = classify_robustness(
        pairs=pairs,
        sign_consistency=sign_consistency,
        expected_seed_count=len(validation_config.seeds),
    )
    checks = build_candidate_robustness_checks(
        pairs=pairs,
        aggregate_statistics=aggregate_statistics,
        expected_seed_count=len(validation_config.seeds),
    )
    return {
        "experiment_id": validation_config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "baseline_config": baseline_config.to_report(),
        "validation_config": validation_config.to_report(),
        "frozen_candidate_definition": validation_config.candidate.to_report(
            experiment_id=validation_config.experiment_id
        ),
        "paired_execution": {
            "seeds": list(validation_config.seeds),
            "duration_s": validation_config.duration_s,
            "same_seed_within_each_pair": True,
            "fresh_fly_world_simulation_per_condition": True,
            "raw_trajectories_stored_in_report": False,
            "gpu_or_rendering_required": False,
        },
        "controlled_variables": {
            "preserved_except_declared_candidate_proxies": True,
            "declared_candidate_proxy_variables": ["motor_scale", "coupling_scale"],
        },
        "pairs": pairs,
        "aggregate_statistics": aggregate_statistics,
        "sign_consistency": sign_consistency,
        "robustness_assessment": robustness_assessment,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_candidate_robustness_unavailable_report(
    error: BaseException,
    *,
    baseline_config: HealthyBaselineConfig,
    validation_config: CandidateRobustnessConfig,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a report for environments where FlyGym execution is unavailable."""

    return {
        "experiment_id": validation_config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "baseline_config": baseline_config.to_report(),
        "validation_config": validation_config.to_report(),
        "frozen_candidate_definition": validation_config.candidate.to_report(
            experiment_id=validation_config.experiment_id
        ),
        "pairs": [],
        "aggregate_statistics": {},
        "sign_consistency": {},
        "robustness_assessment": {
            "classification": "UNSTABLE",
            "reason": "Milestone E3 could not execute in this environment.",
        },
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_aggregate_statistics(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate baseline, candidate, and paired-delta key metrics."""

    completed = [pair for pair in pairs if pair.get("status") == "completed"]
    metrics = {}
    for metric in KEY_METRICS:
        metrics[metric] = {
            "baseline": _stats(
                _metric_values(completed, metric, field="baseline")
            ),
            "candidate": _stats(
                _metric_values(completed, metric, field="candidate")
            ),
            "absolute_delta": _stats(
                _metric_values(completed, metric, field="absolute_delta")
            ),
            "relative_delta": _stats(
                _metric_values(completed, metric, field="relative_delta"),
                allow_missing=True,
            ),
        }
    return {
        "seed_count": len(pairs),
        "completed_seed_count": len(completed),
        "standard_deviation_definition": "population_standard_deviation",
        "metrics": metrics,
    }


def build_sign_consistency(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    """Report sign consistency for selected paired deltas."""

    completed = [pair for pair in pairs if pair.get("status") == "completed"]
    metric_map = {
        "speed_delta": "mean_planar_speed_mm_s",
        "displacement_delta": "planar_displacement_mm",
        "trajectory_efficiency_delta": "trajectory_efficiency",
        "yaw_abs_change_delta": "heading_yaw_abs_change_rad",
    }
    metrics = {
        label: _sign_counts(
            [
                _metric_delta(pair, metric)
                for pair in completed
            ]
        )
        for label, metric in metric_map.items()
    }
    return {
        "seed_count": len(pairs),
        "completed_seed_count": len(completed),
        "metrics": metrics,
        "number_of_seeds_negative_speed_delta": metrics["speed_delta"]["negative"],
        "number_of_seeds_negative_displacement_delta": metrics[
            "displacement_delta"
        ]["negative"],
        "number_of_seeds_negative_trajectory_efficiency_delta": metrics[
            "trajectory_efficiency_delta"
        ]["negative"],
        "number_of_seeds_positive_yaw_abs_change_delta": metrics[
            "yaw_abs_change_delta"
        ]["positive"],
    }


def classify_robustness(
    *,
    pairs: list[dict[str, Any]],
    sign_consistency: dict[str, Any],
    expected_seed_count: int,
) -> dict[str, Any]:
    """Classify the computational candidate as ROBUST, MIXED, or UNSTABLE."""

    completed = [pair for pair in pairs if pair.get("status") == "completed"]
    stable = (
        len(completed) == expected_seed_count
        and all(pair.get("overall_pass") is True for pair in completed)
        and all(_candidate_locomotes(pair) for pair in completed)
    )
    if not stable:
        return {
            "classification": "UNSTABLE",
            "criteria": _classification_criteria(),
            "reason": (
                "At least one paired simulation failed, had non-finite required "
                "metrics, failed validation checks, or did not locomote."
            ),
        }
    negative_speed = sign_consistency["number_of_seeds_negative_speed_delta"]
    negative_displacement = sign_consistency[
        "number_of_seeds_negative_displacement_delta"
    ]
    if negative_speed == expected_seed_count and negative_displacement == expected_seed_count:
        return {
            "classification": "ROBUST",
            "criteria": _classification_criteria(),
            "reason": (
                "All simulations remained stable and key locomotor-output deltas "
                "were consistently lower in the candidate than the paired baseline."
            ),
        }
    return {
        "classification": "MIXED",
        "criteria": _classification_criteria(),
        "reason": (
            "Simulations remained stable, but key locomotor-output delta direction "
            "was not consistent across all seeds."
        ),
    }


def build_candidate_robustness_checks(
    *,
    pairs: list[dict[str, Any]],
    aggregate_statistics: dict[str, Any],
    expected_seed_count: int,
) -> dict[str, dict[str, Any]]:
    """Build software/simulation PASS checks for E3."""

    completed = [pair for pair in pairs if pair.get("status") == "completed"]
    return {
        "seed_pair_count": _check(expected_seed_count, len(pairs)),
        "all_seed_pairs_completed": _check(expected_seed_count, len(completed)),
        "all_pair_checks_passed": _check(
            True,
            all(pair.get("overall_pass") is True for pair in completed),
        ),
        "all_required_observations_finite": _check(
            True,
            all(pair.get("checks", {}).get("required_observations_finite", {}).get("observed") is True for pair in completed),
        ),
        "all_required_metrics_finite": _check(
            True,
            all(pair.get("checks", {}).get("required_metrics_finite", {}).get("observed") is True for pair in completed),
        ),
        "controlled_variables_preserved": _check(
            True,
            all(pair.get("controlled_variables", {}).get("match") is True for pair in completed),
        ),
        "candidate_transformation_validated": _check(
            True,
            all(pair.get("checks", {}).get("candidate_transformation_validated", {}).get("observed") is True for pair in completed),
        ),
        "aggregate_report_produced": _check(
            True,
            bool(aggregate_statistics.get("metrics")),
        ),
    }


def _run_seed_pair(
    *,
    baseline_config: HealthyBaselineConfig,
    validation_config: CandidateRobustnessConfig,
    seed: int,
    runner: ConditionRunner,
) -> dict[str, Any]:
    seed_config = _config_with_seed_and_duration(
        baseline_config,
        seed=seed,
        duration_s=validation_config.duration_s,
    )
    perturbation = validation_config.candidate.perturbation(
        experiment_id=validation_config.experiment_id
    )
    baseline_condition_id = f"seed_{seed}_baseline"
    candidate_condition_id = f"seed_{seed}_candidate_motor_080_coupling_075"

    baseline_result = _safe_run_condition(
        runner,
        seed_config,
        None,
        baseline_condition_id,
    )
    candidate_result = _safe_run_condition(
        runner,
        seed_config,
        perturbation,
        candidate_condition_id,
    )
    base = {
        "seed": seed,
        "baseline_condition_id": baseline_condition_id,
        "candidate_condition_id": candidate_condition_id,
        "same_seed_within_pair": True,
        "duration_s": validation_config.duration_s,
    }
    if baseline_result["status"] != "completed" or candidate_result["status"] != "completed":
        return {
            **base,
            "status": "error",
            "overall_pass": False,
            "baseline": baseline_result,
            "candidate": candidate_result,
        }

    baseline_report = baseline_result["report"]
    candidate_report = candidate_result["report"]
    comparison = compare_locomotion_reports(baseline_report, candidate_report)
    key_metrics = _key_metric_summary(baseline_report, candidate_report, comparison)
    controlled = {
        "baseline": build_controlled_variables(seed_config),
        "candidate": build_controlled_variables(seed_config),
    }
    controlled["match"] = controlled["baseline"] == controlled["candidate"]
    checks = _pair_checks(
        baseline_report=baseline_report,
        candidate_report=candidate_report,
        perturbation_metadata=perturbation.metadata(),
        controlled_variables_match=controlled["match"],
        key_metrics=key_metrics,
    )
    return {
        **base,
        "status": "completed",
        "controlled_variables": controlled,
        "baseline": baseline_report,
        "candidate": candidate_report,
        "comparison": comparison,
        "key_metrics": key_metrics,
        "adhesion": comparison["adhesion"],
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
    }


def _safe_run_condition(
    runner: ConditionRunner,
    config: HealthyBaselineConfig,
    perturbation: Perturbation | None,
    condition_id: str,
) -> dict[str, Any]:
    try:
        return {
            "status": "completed",
            "report": runner(config, perturbation, condition_id),
        }
    except Exception as exc:
        return {
            "status": "error",
            "overall_pass": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def _pair_checks(
    *,
    baseline_report: dict[str, Any],
    candidate_report: dict[str, Any],
    perturbation_metadata: dict[str, Any],
    controlled_variables_match: bool,
    key_metrics: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    baseline_metrics = baseline_report.get("derived_locomotion_metrics", {})
    candidate_metrics = candidate_report.get("derived_locomotion_metrics", {})
    action_transform = candidate_report.get("action_transformation_summary", {})
    action_structural = action_transform.get("structural_checks", {})
    controller_transform = candidate_report.get("controller_transformation_summary", {})
    controller_structural = controller_transform.get("structural_checks", {})
    candidate_transform_valid = (
        perturbation_metadata_complete(perturbation_metadata)
        and action_transform.get("effective_joint_angle_scale")
        == FROZEN_CANDIDATE_MOTOR_SCALE
        and action_transform.get("action_dimensions_valid") is True
        and action_transform.get("adhesion_commands_preserved") is True
        and controller_transform.get("effective_cpg_coupling_scale")
        == FROZEN_CANDIDATE_COUPLING_SCALE
        and controller_transform.get("controller_dimensions_valid") is True
        and action_structural.get(
            "joint_angle_transform_matches_expected", {}
        ).get("observed") is True
        and controller_structural.get(
            "cpg_coupling_transform_matches_expected", {}
        ).get("observed") is True
    )
    return {
        "baseline_simulation_passed": _check(True, baseline_report.get("overall_pass")),
        "candidate_simulation_passed": _check(True, candidate_report.get("overall_pass")),
        "same_seed_within_pair": _check(
            baseline_report.get("configuration", {}).get("random_seed"),
            candidate_report.get("configuration", {}).get("random_seed"),
        ),
        "controlled_variables_match": _check(True, controlled_variables_match),
        "baseline_observations_finite": _check(
            True,
            baseline_metrics.get("observations_are_finite"),
        ),
        "candidate_observations_finite": _check(
            True,
            candidate_metrics.get("observations_are_finite"),
        ),
        "baseline_metrics_finite": _check(
            True,
            baseline_metrics.get("derived_metrics_are_finite"),
        ),
        "candidate_metrics_finite": _check(
            True,
            candidate_metrics.get("derived_metrics_are_finite"),
        ),
        "required_observations_finite": _check(
            True,
            baseline_metrics.get("observations_are_finite") is True
            and candidate_metrics.get("observations_are_finite") is True,
        ),
        "required_metrics_finite": _check(
            True,
            _key_metrics_are_finite(key_metrics),
        ),
        "candidate_transformation_validated": _check(
            True,
            candidate_transform_valid,
        ),
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
    data["experiment_id"] = f"{baseline_config.experiment_id}_e3_seed_{seed}"
    return HealthyBaselineConfig.from_mapping(data)


def _key_metric_summary(
    baseline_report: dict[str, Any],
    candidate_report: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    scalars = {
        metric: _normalise_pair_scalar(values)
        for metric, values in comparison["scalars"].items()
    }
    baseline_yaw_abs = abs(
        float(baseline_report["derived_locomotion_metrics"]["heading_yaw_change_rad"])
    )
    candidate_yaw_abs = abs(
        float(candidate_report["derived_locomotion_metrics"]["heading_yaw_change_rad"])
    )
    scalars["heading_yaw_abs_change_rad"] = _scalar_delta(
        baseline_yaw_abs,
        candidate_yaw_abs,
    )
    return {
        metric: scalars[metric]
        for metric in KEY_METRICS
        if metric in scalars
    }


def _normalise_pair_scalar(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "baseline": values.get("baseline"),
        "candidate": values.get("candidate", values.get("perturbed")),
        "absolute_delta": values.get("absolute_delta"),
        "relative_delta": values.get("relative_delta"),
    }


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


def _metric_values(
    pairs: list[dict[str, Any]],
    metric: str,
    *,
    field: str,
) -> list[float | None]:
    return [
        _finite_or_none(pair.get("key_metrics", {}).get(metric, {}).get(field))
        for pair in pairs
    ]


def _metric_delta(pair: dict[str, Any], metric: str) -> float | None:
    return _finite_or_none(
        pair.get("key_metrics", {}).get(metric, {}).get("absolute_delta")
    )


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


def _sign_counts(values: list[float | None]) -> dict[str, Any]:
    finite = [value for value in values if value is not None and math.isfinite(value)]
    negative = sum(1 for value in finite if value < 0)
    positive = sum(1 for value in finite if value > 0)
    zero = sum(1 for value in finite if value == 0)
    return {
        "count": len(finite),
        "negative": negative,
        "positive": positive,
        "zero": zero,
        "all_negative": bool(finite) and negative == len(finite),
        "all_positive": bool(finite) and positive == len(finite),
    }


def _median(sorted_values: list[float]) -> float:
    midpoint = len(sorted_values) // 2
    if len(sorted_values) % 2 == 1:
        return sorted_values[midpoint]
    return (sorted_values[midpoint - 1] + sorted_values[midpoint]) / 2


def _candidate_locomotes(pair: dict[str, Any]) -> bool:
    metrics = pair.get("candidate", {}).get("derived_locomotion_metrics", {})
    displacement = _finite_or_none(metrics.get("planar_displacement_mm"))
    speed = _finite_or_none(metrics.get("mean_planar_speed_mm_s"))
    trajectory_efficiency = _finite_or_none(metrics.get("trajectory_efficiency"))
    return (
        displacement is not None
        and displacement > 0
        and speed is not None
        and speed > 0
        and trajectory_efficiency is not None
    )


def _key_metrics_are_finite(key_metrics: dict[str, Any]) -> bool:
    for metric in KEY_METRICS:
        if metric not in key_metrics:
            return False
        values = key_metrics[metric]
        for field in ("baseline", "candidate", "absolute_delta"):
            value = _finite_or_none(values.get(field))
            if value is None:
                return False
    return True


def _classification_criteria() -> dict[str, Any]:
    return {
        "ROBUST": (
            "All paired simulations complete, all validation checks pass, "
            "candidate locomotes, and speed/displacement deltas are negative "
            "for every seed."
        ),
        "MIXED": (
            "All simulations remain stable, but key locomotor-output direction "
            "is not consistent across all seeds."
        ),
        "UNSTABLE": (
            "At least one paired simulation fails validation, has non-finite "
            "required metrics, or the candidate does not locomote."
        ),
        "classification_scope": (
            "Software/simulation robustness only; not Parkinson severity and not "
            "biological statistical significance."
        ),
    }


def _scalar_delta(baseline: Any, candidate: Any) -> dict[str, float | None]:
    baseline_value = _finite_or_none(baseline)
    candidate_value = _finite_or_none(candidate)
    if baseline_value is None or candidate_value is None:
        return {
            "baseline": baseline_value,
            "candidate": candidate_value,
            "absolute_delta": None,
            "relative_delta": None,
        }
    absolute_delta = candidate_value - baseline_value
    return {
        "baseline": baseline_value,
        "candidate": candidate_value,
        "absolute_delta": absolute_delta,
        "relative_delta": (
            None
            if abs(baseline_value) <= 1e-9
            else absolute_delta / abs(baseline_value)
        ),
    }


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
    "CandidateRobustnessConfig",
    "E3CandidateDefinition",
    "FROZEN_CANDIDATE_COUPLING_SCALE",
    "FROZEN_CANDIDATE_MOTOR_SCALE",
    "KEY_METRICS",
    "SCIENTIFIC_SCOPE",
    "build_aggregate_statistics",
    "build_candidate_robustness_checks",
    "build_candidate_robustness_report",
    "build_candidate_robustness_unavailable_report",
    "build_sign_consistency",
    "classify_robustness",
    "load_candidate_robustness_config",
    "run_candidate_robustness_validation",
]
