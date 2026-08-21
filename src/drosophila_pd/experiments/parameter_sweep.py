"""Parameter-response sweeps for Milestone E0/E1."""

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
    Perturbation,
    perturbation_from_mapping,
    perturbation_metadata_complete,
)


SCIENTIFIC_SCOPE = (
    "Milestone E0/E1 characterizes generic parameter-response sweeps for "
    "phenomenological motor-vigor and coordination proxies. These perturbations "
    "are not direct simulations of dopamine concentration, dopaminergic neuron "
    "loss, or a Parkinson's disease condition, and they are not biological "
    "validation."
)

FORBIDDEN_SWEEP_TERMS = ("dopamine", "pd_stage", "parkinson_severity")

SCALAR_RESPONSE_METRICS = (
    "planar_displacement_mm",
    "mean_planar_speed_mm_s",
    "heading_yaw_change_rad",
    "body_height_min_mm",
    "body_height_mean_mm",
    "body_height_range_mm",
    "joint_angle_action_mean",
    "joint_angle_action_abs_mean",
)

ConditionRunner = Callable[
    [HealthyBaselineConfig, Perturbation | None, str], dict[str, Any]
]


@dataclass(frozen=True)
class SweepConditionSpec:
    """One generated condition in a parameter-response sweep."""

    condition_id: str
    family: str
    perturbation_type: str
    parameter_name: str
    parameter_value: float
    baseline_equivalent_value: float
    perturbation: Perturbation

    @property
    def baseline_equivalent(self) -> bool:
        return math.isclose(
            self.parameter_value,
            self.baseline_equivalent_value,
            rel_tol=0.0,
            abs_tol=1e-12,
        )

    def to_report(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "family": self.family,
            "perturbation_type": self.perturbation_type,
            "parameter_name": self.parameter_name,
            "parameter_value": self.parameter_value,
            "baseline_equivalent_value": self.baseline_equivalent_value,
            "baseline_equivalent": self.baseline_equivalent,
            "perturbation": self.perturbation.metadata(),
        }


@dataclass(frozen=True)
class SweepFamilyConfig:
    """Configuration for one perturbation family in a sweep."""

    family: str
    perturbation_type: str
    parameter_name: str
    values: tuple[float, ...]
    baseline_equivalent_value: float
    description: str | None = None

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "SweepFamilyConfig":
        family = _require_name(data, "family")
        perturbation_type = _require_name(data, "perturbation_type")
        parameter_name = _require_name(data, "parameter_name")
        raw_values = data.get("values")
        if not isinstance(raw_values, list) or not raw_values:
            raise ValueError("Sweep family values must be a non-empty list.")
        values = tuple(_finite_float(value, "values") for value in raw_values)
        baseline_equivalent_value = _finite_float(
            data.get("baseline_equivalent_value", 1.0),
            "baseline_equivalent_value",
        )
        config = cls(
            family=family,
            perturbation_type=perturbation_type,
            parameter_name=parameter_name,
            values=values,
            baseline_equivalent_value=baseline_equivalent_value,
            description=data.get("description"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        _reject_forbidden_terms(self.family)
        if self.perturbation_type not in {
            "global_action_scale",
            "cpg_coupling_scale",
        }:
            raise ValueError(f"Unsupported sweep perturbation type: {self.perturbation_type}")
        if self.parameter_name != "scale":
            raise ValueError("Milestone E0/E1 sweep families currently use scale.")
        if not any(
            math.isclose(value, self.baseline_equivalent_value, abs_tol=1e-12)
            for value in self.values
        ):
            raise ValueError(
                f"Sweep family {self.family} must include its baseline-equivalent value."
            )

    def conditions(self, *, experiment_id: str) -> list[SweepConditionSpec]:
        return [
            self._condition(value, experiment_id=experiment_id)
            for value in self.values
        ]

    def to_report(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "perturbation_type": self.perturbation_type,
            "parameter_name": self.parameter_name,
            "values": list(self.values),
            "baseline_equivalent_value": self.baseline_equivalent_value,
            "description": self.description,
        }

    def _condition(
        self, value: float, *, experiment_id: str
    ) -> SweepConditionSpec:
        condition_id = f"{self.family}_{self.parameter_name}_{_scale_suffix(value)}"
        perturbation = perturbation_from_mapping(
            {
                "experiment_id": experiment_id,
                "type": self.perturbation_type,
                "name": condition_id,
                self.parameter_name: value,
            }
        )
        return SweepConditionSpec(
            condition_id=condition_id,
            family=self.family,
            perturbation_type=self.perturbation_type,
            parameter_name=self.parameter_name,
            parameter_value=float(value),
            baseline_equivalent_value=self.baseline_equivalent_value,
            perturbation=perturbation,
        )


@dataclass(frozen=True)
class ParameterSweepConfig:
    """Validated Milestone E0/E1 parameter sweep configuration."""

    experiment_id: str
    families: tuple[SweepFamilyConfig, ...]
    scientific_frame: dict[str, Any]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "ParameterSweepConfig":
        experiment_id = _require_name(data, "experiment_id")
        _reject_forbidden_terms(experiment_id)
        raw_families = data.get("families")
        if not isinstance(raw_families, list) or not raw_families:
            raise ValueError("Sweep configuration requires at least one family.")
        families = tuple(
            SweepFamilyConfig.from_mapping(item) for item in raw_families
        )
        config = cls(
            experiment_id=experiment_id,
            families=families,
            scientific_frame=dict(data.get("scientific_frame") or {}),
        )
        config.validate()
        return config

    def validate(self) -> None:
        family_names = [family.family for family in self.families]
        if len(set(family_names)) != len(family_names):
            raise ValueError("Sweep family names must be unique.")

    def conditions(self) -> list[SweepConditionSpec]:
        conditions: list[SweepConditionSpec] = []
        for family in self.families:
            conditions.extend(family.conditions(experiment_id=self.experiment_id))
        return conditions

    def to_report(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "families": [family.to_report() for family in self.families],
            "scientific_frame": self.scientific_frame,
        }


def load_parameter_sweep_config(path: str | Path) -> ParameterSweepConfig:
    """Load a Milestone E0/E1 sweep YAML file."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Sweep configuration root must be a mapping.")
    return ParameterSweepConfig.from_mapping(loaded)


def run_parameter_sweep(
    *,
    baseline_config: HealthyBaselineConfig,
    sweep_config: ParameterSweepConfig,
    repo_root: str | Path | None = None,
    condition_runner: ConditionRunner | None = None,
) -> dict[str, Any]:
    """Run baseline once, then every configured perturbation condition."""

    runner = condition_runner or _default_condition_runner(repo_root=repo_root)
    baseline_report = runner(baseline_config, None, "baseline")
    conditions = []
    for spec in sweep_config.conditions():
        conditions.append(
            _run_condition(
                baseline_config=baseline_config,
                baseline_report=baseline_report,
                spec=spec,
                runner=runner,
            )
        )
    return build_parameter_sweep_report(
        baseline_config=baseline_config,
        sweep_config=sweep_config,
        baseline_report=baseline_report,
        conditions=conditions,
        repo_root=repo_root,
    )


def build_parameter_sweep_report(
    *,
    baseline_config: HealthyBaselineConfig,
    sweep_config: ParameterSweepConfig,
    baseline_report: dict[str, Any],
    conditions: list[dict[str, Any]],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a combined JSON-serializable parameter sweep report."""

    response_curves = build_response_curves(conditions)
    checks = build_sweep_checks(
        baseline_report=baseline_report,
        conditions=conditions,
        expected_condition_count=len(sweep_config.conditions()),
    )
    return {
        "experiment_id": sweep_config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "baseline_config": baseline_config.to_report(),
        "sweep_config": sweep_config.to_report(),
        "source_api_findings": _source_api_findings(),
        "baseline": baseline_report,
        "conditions": conditions,
        "response_curves": response_curves,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_parameter_sweep_unavailable_report(
    error: BaseException,
    *,
    baseline_config: HealthyBaselineConfig,
    sweep_config: ParameterSweepConfig,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a report for environments where FlyGym execution is unavailable."""

    return {
        "experiment_id": sweep_config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "baseline_config": baseline_config.to_report(),
        "sweep_config": sweep_config.to_report(),
        "conditions": [],
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_response_curves(conditions: list[dict[str, Any]]) -> dict[str, Any]:
    """Build family-wise parameter response curves from completed conditions."""

    by_family: dict[str, list[dict[str, Any]]] = {}
    for condition in conditions:
        if condition.get("status") != "completed":
            continue
        by_family.setdefault(condition["family"], []).append(condition)

    curves = {}
    for family, family_conditions in by_family.items():
        metric_curves = {
            metric: _metric_curve(family_conditions, metric)
            for metric in SCALAR_RESPONSE_METRICS
        }
        curves[family] = {
            "parameter_name": family_conditions[0]["parameter_name"],
            "perturbation_type": family_conditions[0]["perturbation_type"],
            "condition_order": [item["condition_id"] for item in family_conditions],
            "metrics": metric_curves,
            "adhesion": _adhesion_curves(family_conditions),
        }
    return curves


def build_sweep_checks(
    *,
    baseline_report: dict[str, Any],
    conditions: list[dict[str, Any]],
    expected_condition_count: int,
) -> dict[str, dict[str, Any]]:
    """Build PASS/FAIL checks for the combined sweep report."""

    completed_count = sum(1 for item in conditions if item.get("status") == "completed")
    failed_count = len(conditions) - completed_count
    baseline_equivalent = [
        item for item in conditions if item.get("baseline_equivalent") is True
    ]
    return {
        "baseline_simulation_passed": _check(True, baseline_report.get("overall_pass")),
        "condition_count": _check(expected_condition_count, len(conditions)),
        "all_conditions_completed": _check(0, failed_count),
        "completed_condition_count": _check(expected_condition_count, completed_count),
        "all_completed_conditions_passed": _check(
            True,
            all(
                item.get("overall_pass") is True
                for item in conditions
                if item.get("status") == "completed"
            ),
        ),
        "baseline_equivalent_conditions_present": _check(
            True, len(baseline_equivalent) > 0
        ),
        "baseline_equivalent_conditions_pass": _check(
            True,
            all(
                item.get("baseline_equivalence", {}).get("pass") is True
                for item in baseline_equivalent
                if item.get("status") == "completed"
            ),
        ),
    }


def _run_condition(
    *,
    baseline_config: HealthyBaselineConfig,
    baseline_report: dict[str, Any],
    spec: SweepConditionSpec,
    runner: ConditionRunner,
) -> dict[str, Any]:
    base = spec.to_report()
    try:
        condition_report = runner(
            baseline_config, spec.perturbation, spec.condition_id
        )
    except Exception as exc:
        return {
            **base,
            "status": "error",
            "overall_pass": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
        }

    controlled = {
        "baseline": build_controlled_variables(baseline_config),
        "condition": build_controlled_variables(
            spec.perturbation.apply_to_config(baseline_config)
        ),
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
        perturbation_metadata=spec.perturbation.metadata(),
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
    transform = condition_report.get("action_transformation_summary", {})
    structural = transform.get("structural_checks", {})
    checks = {
        "baseline_simulation_passed": _check(True, baseline_report.get("overall_pass")),
        "condition_simulation_passed": _check(True, condition_report.get("overall_pass")),
        "controlled_variables_match": _check(True, controlled_variables_match),
        "perturbation_metadata_complete": _check(
            True, perturbation_metadata_complete(perturbation_metadata)
        ),
        "observations_finite": _check(True, metrics.get("observations_are_finite")),
        "metrics_finite": _check(True, metrics.get("derived_metrics_are_finite")),
        "expected_step_count": _check(expected_step_count, metrics.get("step_count")),
        "action_dimensions_valid": _check(
            True, transform.get("action_dimensions_valid")
        ),
        "joint_angle_transform_matches_expected": _check(
            True,
            structural.get(
                "joint_angle_transform_matches_expected", {}
            ).get("observed"),
        ),
        "adhesion_commands_preserved": _check(
            True, transform.get("adhesion_commands_preserved")
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


def _metric_curve(
    conditions: list[dict[str, Any]], metric: str
) -> dict[str, Any]:
    points = []
    values = []
    for condition in conditions:
        scalar = condition["comparison"]["scalars"][metric]
        value = scalar["perturbed"]
        values.append(value)
        points.append(
            {
                "condition_id": condition["condition_id"],
                "parameter_value": condition["parameter_value"],
                "metric_value": value,
                "baseline_value": scalar["baseline"],
                "absolute_delta": scalar["absolute_delta"],
                "relative_delta": scalar["relative_delta"],
                "baseline_equivalent": condition["baseline_equivalent"],
            }
        )
    return {
        "points": points,
        "observed_monotonicity": _observed_monotonicity(values),
    }


def _adhesion_curves(conditions: list[dict[str, Any]]) -> dict[str, Any]:
    if not conditions:
        return {"available": False}
    first = conditions[0]["comparison"]["adhesion"]
    if not first.get("available"):
        return {"available": False}
    leg_order = first["leg_order"]
    return {
        "available": True,
        "leg_order": leg_order,
        "duty_factor_delta_by_condition": [
            {
                "condition_id": condition["condition_id"],
                "parameter_value": condition["parameter_value"],
                "delta_by_leg": condition["comparison"]["adhesion"][
                    "duty_factor_delta_by_leg"
                ],
            }
            for condition in conditions
        ],
        "transition_count_delta_by_condition": [
            {
                "condition_id": condition["condition_id"],
                "parameter_value": condition["parameter_value"],
                "delta_by_leg": condition["comparison"]["adhesion"][
                    "transition_count_delta_by_leg"
                ],
            }
            for condition in conditions
        ],
    }


def _observed_monotonicity(values: list[Any]) -> str:
    finite_values = [_finite_or_none(value) for value in values]
    if any(value is None for value in finite_values) or len(finite_values) < 2:
        return "unavailable"
    diffs = [
        float(right) - float(left)
        for left, right in zip(finite_values, finite_values[1:])
    ]
    tol = 1e-12
    if all(abs(diff) <= tol for diff in diffs):
        return "constant"
    if all(diff >= -tol for diff in diffs):
        return "nondecreasing_in_config_order"
    if all(diff <= tol for diff in diffs):
        return "nonincreasing_in_config_order"
    return "non_monotonic_in_config_order"


def _source_api_findings() -> dict[str, Any]:
    return {
        "flygym_version_inspected": "2.1.0",
        "controller_source": "flygym_demo.complex_terrain.cpg_controller",
        "cpg_network_class": "flygym_demo.complex_terrain.CPGNetwork",
        "coordination_intervention": "cpg_network.coupling_weights scale",
        "source_basis": (
            "CPGNetwork.step passes self.coupling_weights into calculate_ddt; "
            "make_tripod_cpg_network initializes coupling_weights as "
            "(phase_biases > 0) * coupling_strength."
        ),
        "unchanged_controller_parameters": [
            "intrinsic_freqs",
            "intrinsic_amps",
            "phase_biases",
            "convergence_coefs",
        ],
    }


def _scale_suffix(value: float) -> str:
    return f"{int(round(float(value) * 100)):03d}"


def _require_name(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string.")
    return value.strip()


def _finite_float(value: Any, name: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _finite_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _reject_forbidden_terms(value: str) -> None:
    lowered = value.lower()
    for term in FORBIDDEN_SWEEP_TERMS:
        if term in lowered:
            raise ValueError(f"Unsupported disease-mapping term in sweep config: {term}")


def _check(expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


__all__ = [
    "ParameterSweepConfig",
    "SCALAR_RESPONSE_METRICS",
    "SCIENTIFIC_SCOPE",
    "SweepConditionSpec",
    "SweepFamilyConfig",
    "build_parameter_sweep_report",
    "build_parameter_sweep_unavailable_report",
    "build_response_curves",
    "build_sweep_checks",
    "load_parameter_sweep_config",
    "run_parameter_sweep",
]
