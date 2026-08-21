"""Reproducible, evidence-only synthesis of frozen milestone reports.

This module never imports FlyGym or MuJoCo. It consumes immutable JSON reports,
validates their software/simulation scope, and derives tables and figures from
the recorded values only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
from typing import Any, Iterable

import yaml

from drosophila_pd.anatomy.audit import git_commit, write_json_report


EVIDENCE_KEYS = (
    "baseline",
    "perturbation_identity",
    "perturbation_action_scale",
    "e1",
    "e2",
    "e3",
    "e4",
    "e5",
)

METRIC_KEYS = (
    "planar_displacement_mm",
    "mean_planar_speed_mm_s",
    "planar_path_length_mm",
    "trajectory_efficiency",
    "heading_yaw_change_rad",
    "body_height_mean_mm",
    "body_height_min_mm",
    "body_height_range_mm",
    "joint_angle_action_abs_mean",
)

PRIMARY_METRICS = ("mean_planar_speed_mm_s", "planar_path_length_mm")

SCIENTIFIC_SCOPE = (
    "Milestone E6 validates internal consistency and reproducible synthesis of "
    "frozen computational evidence. It does not validate a Parkinson's disease "
    "model, establish biological realism, or make claims about real flies."
)

SUPPORTED_COMPUTATIONAL_FINDINGS = (
    "Reduced motor-command scaling lowers simulated locomotor output.",
    "Reduced CPG coupling affects simulated locomotor output and directionality.",
    "The frozen combined candidate shows multi-seed simulated locomotor-output reduction.",
    "E5 demonstrates computational reversibility, particularly along the motor axis.",
)

LITERATURE_GROUNDED_FINDINGS = (
    "E4 reports directional qualitative concordance for selected adult walking speed and distance endpoints.",
)

NOT_ESTABLISHED = (
    "validated Parkinson's disease model",
    "dopamine depletion equivalence",
    "neuron-loss mapping",
    "pharmacological or L-DOPA simulation",
    "biological rescue",
    "mechanistic equivalence",
    "disease severity calibration",
    "statistical significance from the frozen reports",
)

PROHIBITED_ARTIFACT_TERMS = (
    "parkinson",
    "dopamine",
    "l-dopa",
    "neuron-loss",
    "treatment",
    "cure",
    "biological validation",
)


class EvidenceValidationError(ValueError):
    """Raised when frozen evidence cannot support an E6 synthesis."""


@dataclass(frozen=True)
class EvidenceSynthesisConfig:
    """Validated paths and fixed E6 analysis settings."""

    experiment_id: str
    required_evidence: dict[str, str]
    frozen_motor_scale: float
    frozen_coupling_scale: float
    figures_dir: str
    tables_dir: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "EvidenceSynthesisConfig":
        if not isinstance(data, dict):
            raise EvidenceValidationError("E6 config must contain a mapping.")
        experiment_id = _required_text(data, "experiment_id")
        evidence = data.get("required_evidence")
        if not isinstance(evidence, dict):
            raise EvidenceValidationError("required_evidence must be a mapping.")
        missing = [key for key in EVIDENCE_KEYS if key not in evidence]
        extra = sorted(set(evidence) - set(EVIDENCE_KEYS))
        if missing or extra:
            raise EvidenceValidationError(
                f"required_evidence keys mismatch; missing={missing}, extra={extra}"
            )
        paths = {
            key: _required_text(evidence, key)
            for key in EVIDENCE_KEYS
        }
        candidate = data.get("frozen_candidate", {})
        if not isinstance(candidate, dict):
            raise EvidenceValidationError("frozen_candidate must be a mapping.")
        return cls(
            experiment_id=experiment_id,
            required_evidence=paths,
            frozen_motor_scale=_finite_float(
                candidate.get("motor_scale"), "frozen_candidate.motor_scale"
            ),
            frozen_coupling_scale=_finite_float(
                candidate.get("coupling_scale"), "frozen_candidate.coupling_scale"
            ),
            figures_dir=_required_text(
                data.get("artifacts", {}), "figures_dir"
            ),
            tables_dir=_required_text(data.get("artifacts", {}), "tables_dir"),
        )


def load_synthesis_config(path: str | Path) -> EvidenceSynthesisConfig:
    """Load and validate the version-controlled E6 YAML configuration."""

    config_path = Path(path)
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise EvidenceValidationError(
            f"Unable to read E6 config {config_path}: {exc}"
        ) from exc
    except yaml.YAMLError as exc:
        raise EvidenceValidationError(
            f"Unable to parse E6 config {config_path}: {exc}"
        ) from exc
    return EvidenceSynthesisConfig.from_mapping(data)


def load_evidence_reports(
    config: EvidenceSynthesisConfig,
    *,
    repo_root: str | Path,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    """Read all configured JSON reports and build an immutable-input manifest."""

    root = Path(repo_root)
    reports: dict[str, dict[str, Any]] = {}
    manifest: list[dict[str, Any]] = []
    errors: list[str] = []
    for key in EVIDENCE_KEYS:
        configured_path = Path(config.required_evidence[key])
        path = configured_path if configured_path.is_absolute() else root / configured_path
        if not path.is_file():
            errors.append(f"{key}: missing evidence file {configured_path}")
            continue
        try:
            raw = path.read_bytes()
            report = json.loads(raw.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"{key}: cannot load {configured_path}: {exc}")
            continue
        if not isinstance(report, dict):
            errors.append(f"{key}: top-level JSON value must be an object")
            continue
        reports[key] = report
        manifest.append(
            {
                "key": key,
                "path": configured_path.as_posix(),
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "experiment_id": report.get("experiment_id"),
                "git_commit": report.get("git_commit"),
                "overall_pass": report.get("overall_pass"),
            }
        )
    if errors:
        raise EvidenceValidationError("; ".join(errors))
    return reports, manifest


def validate_frozen_evidence(
    reports: dict[str, dict[str, Any]],
    *,
    config: EvidenceSynthesisConfig,
) -> dict[str, dict[str, Any]]:
    """Validate required frozen-report state and cross-report candidate identity."""

    checks: dict[str, dict[str, Any]] = {}
    for key in EVIDENCE_KEYS:
        if key not in reports:
            raise EvidenceValidationError(f"Missing loaded report: {key}")

    required_top_keys = {
        "baseline": ("derived_locomotion_metrics", "simulation_summary"),
        "perturbation_identity": ("baseline", "perturbed", "comparison"),
        "perturbation_action_scale": ("baseline", "perturbed", "comparison"),
        "e1": ("conditions", "response_curves"),
        "e2": ("conditions", "interaction_analysis"),
        "e3": ("pairs", "aggregate_statistics", "frozen_candidate_definition"),
        "e4": ("e3_simulation_phenotype", "overall_scientific_status"),
        "e5": ("seed_runs", "condition_assessments", "preregistered_design"),
    }
    for key, required in required_top_keys.items():
        _add_check(
            checks,
            f"{key}_schema_keys_present",
            True,
            all(name in reports[key] for name in required),
        )
        _add_check(
            checks,
            f"{key}_overall_pass",
            True,
            reports[key].get("overall_pass") is True,
        )
        _add_check(
            checks,
            f"{key}_git_provenance_present",
            True,
            _nonempty_text(reports[key].get("git_commit")),
        )

    for key in EVIDENCE_KEYS:
        _add_check(
            checks,
            f"{key}_all_top_level_checks_pass",
            True,
            _all_checks_pass(reports[key]),
        )

    for key, expected_environment in (
        ("baseline", reports["baseline"]),
        ("perturbation_identity", reports["perturbation_identity"].get("environment", {})),
        ("perturbation_action_scale", reports["perturbation_action_scale"].get("environment", {})),
        ("e1", reports["e1"].get("environment", {})),
        ("e2", reports["e2"].get("environment", {})),
        ("e3", reports["e3"].get("environment", {})),
        ("e5", reports["e5"].get("environment", {})),
    ):
        _add_check(
            checks,
            f"{key}_environment_target",
            {"python": "3.12", "flygym": "2.1.0", "mujoco": "3.9.0"},
            {
                "python": str(expected_environment.get("python_major_minor")),
                "flygym": expected_environment.get("flygym_version"),
                "mujoco": expected_environment.get("mujoco_version"),
            },
        )

    e1_conditions = reports["e1"].get("conditions", [])
    _add_check(checks, "e1_condition_count", 10, len(e1_conditions))
    _add_check(
        checks,
        "e1_conditions_completed_and_passed",
        True,
        _all_condition_reports_pass(e1_conditions),
    )
    e2_conditions = reports["e2"].get("conditions", [])
    _add_check(checks, "e2_condition_count", 9, len(e2_conditions))
    _add_check(
        checks,
        "e2_conditions_completed_and_passed",
        True,
        _all_condition_reports_pass(e2_conditions),
    )
    e3_pairs = reports["e3"].get("pairs", [])
    _add_check(checks, "e3_seed_pair_count", 5, len(e3_pairs))
    _add_check(
        checks,
        "e3_seed_pairs_completed_and_passed",
        True,
        _all_condition_reports_pass(e3_pairs),
    )
    e5_seed_runs = reports["e5"].get("seed_runs", [])
    _add_check(checks, "e5_seed_run_count", 5, len(e5_seed_runs))
    _add_check(
        checks,
        "e5_seed_runs_completed_and_passed",
        True,
        all(
            run.get("status") == "completed"
            and run.get("overall_pass") is True
            and all(item.get("overall_pass") is True for item in run.get("conditions", []))
            for run in e5_seed_runs
        ),
    )

    expected_motor = config.frozen_motor_scale
    expected_coupling = config.frozen_coupling_scale
    e3_candidate = reports["e3"].get("frozen_candidate_definition", {})
    e4_phenotype = reports["e4"].get("e3_simulation_phenotype", {})
    e4_candidate = e4_phenotype.get("frozen_candidate", {})
    e5_candidate = reports["e5"].get("preregistered_design", {}).get("frozen_impaired_candidate", {})
    _add_check(
        checks,
        "frozen_candidate_e3",
        {"motor_scale": expected_motor, "coupling_scale": expected_coupling},
        _candidate_pair(e3_candidate),
    )
    _add_check(
        checks,
        "frozen_candidate_e4",
        {"motor_scale": expected_motor, "coupling_scale": expected_coupling},
        _candidate_pair(e4_candidate),
    )
    _add_check(
        checks,
        "frozen_candidate_e5",
        {"motor_scale": expected_motor, "coupling_scale": expected_coupling},
        _candidate_pair(e5_candidate),
    )
    e2_candidate = next(
        (
            {
                "motor_scale": item.get("motor_scale"),
                "coupling_scale": item.get("coupling_scale"),
            }
            for item in e2_conditions
            if item.get("condition_id") == "combined_motor_080_coupling_075"
        ),
        None,
    )
    _add_check(
        checks,
        "frozen_candidate_e2_condition_present",
        {"motor_scale": expected_motor, "coupling_scale": expected_coupling},
        e2_candidate,
    )
    _add_check(
        checks,
        "e4_references_e3_provenance",
        reports["e3"].get("git_commit"),
        e4_phenotype.get("source_git_commit"),
    )
    _add_check(
        checks,
        "e4_references_passing_e3",
        True,
        e4_phenotype.get("source_overall_pass") is True,
    )
    _add_check(
        checks,
        "scientific_boundary_fields_present",
        True,
        all(
            isinstance(reports[key].get("scientific_scope"), str)
            and reports[key]["scientific_scope"].strip()
            for key in EVIDENCE_KEYS
            if key != "e4"
        )
        and isinstance(reports["e4"].get("scientific_scope"), str),
    )

    failed = [name for name, check in checks.items() if not check["pass"]]
    if failed:
        raise EvidenceValidationError(
            "Frozen evidence validation failed: " + ", ".join(failed)
        )
    return checks


def build_synthesis(
    reports: dict[str, dict[str, Any]],
    manifest: list[dict[str, Any]],
    *,
    config: EvidenceSynthesisConfig,
    repo_root: str | Path,
    validation_checks: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the machine-readable E6 synthesis without running simulations."""

    checks = validation_checks or validate_frozen_evidence(reports, config=config)
    labels = _artifact_labels()
    return {
        "experiment_id": config.experiment_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "provenance": {
            "synthesis_git_commit": git_commit(repo_root),
            "synthesis_worktree_dirty": _git_worktree_dirty(repo_root),
            "input_git_commits": {
                item["key"]: item.get("git_commit") for item in manifest
            },
            "config_path": "configs/analysis/milestone_e6.yaml",
        },
        "input_evidence_manifest": manifest,
        "milestone_status": {
            "C": "FROZEN",
            "D": "FROZEN",
            "E1": "FROZEN",
            "E2": "FROZEN",
            "E3": "FROZEN",
            "E4": "FROZEN",
            "E5": "FROZEN",
            "E6": "IMPLEMENTED_AWAITING_REVIEW",
        },
        "frozen_candidate_definition": {
            "motor_scale": config.frozen_motor_scale,
            "coupling_scale": config.frozen_coupling_scale,
            "selection_basis": "Frozen E2/E3 computational candidate; no E6 tuning.",
        },
        "baseline_numerical_summary": _baseline_summary(reports["baseline"]),
        "e1_parameter_response_summary": _e1_summary(reports["e1"]),
        "e2_interaction_summary": _e2_summary(reports["e2"]),
        "e3_robustness_summary": _e3_summary(reports["e3"]),
        "e4_concordance_summary": _e4_summary(reports["e4"]),
        "e5_reversibility_summary": _e5_summary(reports["e5"]),
        "scientific_synthesis": {
            "supported_computational_findings": list(SUPPORTED_COMPUTATIONAL_FINDINGS),
            "literature_grounded_qualitative_findings": list(LITERATURE_GROUNDED_FINDINGS),
            "not_established": list(NOT_ESTABLISHED),
            "scope": SCIENTIFIC_SCOPE,
        },
        "artifact_labels": labels,
        "artifacts": {
            "figures": [],
            "tables": [],
        },
        "checks": checks,
        "scientific_scope": SCIENTIFIC_SCOPE,
        "overall_pass": all(item["pass"] for item in checks.values()),
    }


def generate_tables(
    synthesis: dict[str, Any],
    *,
    output_dir: str | Path,
) -> list[str]:
    """Generate compact CSV tables from synthesis values only."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    tables: list[tuple[str, list[dict[str, Any]]]] = [
        ("evidence_manifest.csv", synthesis["input_evidence_manifest"]),
        ("e1_parameter_response.csv", _e1_rows(synthesis["e1_parameter_response_summary"])),
        ("e2_condition_summary.csv", synthesis["e2_interaction_summary"]["condition_summary"]),
        ("e3_seed_summary.csv", synthesis["e3_robustness_summary"]["seed_summary"]),
        ("e5_reversibility_summary.csv", synthesis["e5_reversibility_summary"]["condition_summary"]),
    ]
    output_paths: list[str] = []
    for filename, rows in tables:
        path = directory / filename
        _write_csv(path, rows)
        output_paths.append(path.as_posix())
    return output_paths


def generate_figures(
    synthesis: dict[str, Any],
    *,
    output_dir: str | Path,
) -> list[str]:
    """Generate four deterministic report figures from synthesis data."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []

    e1 = synthesis["e1_parameter_response_summary"]["families"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    for family, color in (("motor_vigor_proxy", "tab:blue"), ("coordination_proxy", "tab:orange")):
        family_data = e1[family]
        x = [
            point["parameter_value"]
            for point in family_data["metrics"]["mean_planar_speed_mm_s"]["points"]
        ]
        speed = [
            point["metric_value"]
            for point in family_data["metrics"]["mean_planar_speed_mm_s"]["points"]
        ]
        displacement = [
            point["metric_value"]
            for point in family_data["metrics"]["planar_displacement_mm"]["points"]
        ]
        axes[0].plot(x, speed, marker="o", color=color, label=family)
        axes[1].plot(x, displacement, marker="o", color=color, label=family)
    axes[0].set_ylabel("Mean planar speed (mm/s)")
    axes[1].set_ylabel("Planar displacement (mm)")
    for axis in axes:
        axis.set_xlabel("Computational proxy scale")
        axis.grid(True, alpha=0.25)
        axis.legend()
    fig.suptitle("E1 computational proxy response curves")
    path = directory / "e1_parameter_response.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    e2_rows = synthesis["e2_interaction_summary"]["condition_summary"]
    selected_ids = [
        "control_motor_100_coupling_100",
        "motor_080_coupling_100",
        "motor_100_coupling_075",
        "combined_motor_080_coupling_075",
    ]
    selected = [next(row for row in e2_rows if row["condition_id"] == item) for item in selected_ids]
    labels = ["control", "motor-only", "coordination-only", "combined"]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
    for axis, metric, ylabel in (
        (axes[0], "mean_planar_speed_mm_s", "Mean planar speed (mm/s)"),
        (axes[1], "planar_displacement_mm", "Planar displacement (mm)"),
    ):
        axis.bar(labels, [row[metric] for row in selected], color=["0.45", "tab:blue", "tab:orange", "tab:green"])
        axis.set_ylabel(ylabel)
        axis.tick_params(axis="x", rotation=25)
        axis.grid(True, axis="y", alpha=0.25)
    fig.suptitle("E2 combined computational condition comparison")
    path = directory / "e2_condition_comparison.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    e3_rows = synthesis["e3_robustness_summary"]["seed_summary"]
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2), constrained_layout=True)
    for axis, metric, ylabel in (
        (axes[0], "mean_planar_speed_mm_s", "Mean planar speed (mm/s)"),
        (axes[1], "planar_path_length_mm", "Planar path length (mm)"),
    ):
        seeds = [row["seed"] for row in e3_rows]
        baseline = [row[f"baseline_{metric}"] for row in e3_rows]
        candidate = [row[f"candidate_{metric}"] for row in e3_rows]
        for seed, base, value in zip(seeds, baseline, candidate):
            axis.plot([seed, seed], [base, value], color="0.7", linewidth=1)
        axis.plot(seeds, baseline, "o-", label="baseline")
        axis.plot(seeds, candidate, "o-", label="frozen candidate")
        axis.set_xlabel("Seed")
        axis.set_ylabel(ylabel)
        axis.grid(True, alpha=0.25)
        axis.legend()
    fig.suptitle("E3 paired multi-seed computational robustness")
    path = directory / "e3_paired_seed_robustness.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)

    e5 = synthesis["e5_reversibility_summary"]
    condition_order = e5["condition_order"]
    condition_labels = e5["condition_labels"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    for axis, metric, ylabel in (
        (axes[0], "mean_planar_speed_mm_s", "Mean planar speed (mm/s)"),
        (axes[1], "planar_path_length_mm", "Planar path length (mm)"),
    ):
        values = [e5["endpoint_means"][metric][condition] for condition in condition_order]
        axis.bar(condition_labels, values, color="tab:green")
        axis.set_ylabel(ylabel)
        axis.tick_params(axis="x", rotation=35)
        axis.grid(True, axis="y", alpha=0.25)
    fig.suptitle("E5 computational reversibility endpoints")
    path = directory / "e5_computational_reversibility.png"
    fig.savefig(path, dpi=160)
    plt.close(fig)
    paths.append(path)
    return [path.as_posix() for path in paths]


def run_evidence_synthesis(
    *,
    config_path: str | Path,
    output_path: str | Path,
    repo_root: str | Path,
) -> dict[str, Any]:
    """Run the complete CPU-only E6 synthesis and write its report."""

    config = load_synthesis_config(config_path)
    reports, manifest = load_evidence_reports(config, repo_root=repo_root)
    checks = validate_frozen_evidence(reports, config=config)
    synthesis = build_synthesis(
        reports,
        manifest,
        config=config,
        repo_root=repo_root,
        validation_checks=checks,
    )
    figures_dir = _resolve_artifact_dir(config.figures_dir, repo_root)
    tables_dir = _resolve_artifact_dir(config.tables_dir, repo_root)
    figure_paths = generate_figures(synthesis, output_dir=figures_dir)
    table_paths = generate_tables(synthesis, output_dir=tables_dir)
    labels = synthesis["artifact_labels"]
    _add_check(synthesis["checks"], "artifact_generation_completed", True, all(Path(path).is_file() for path in figure_paths + table_paths))
    _add_check(synthesis["checks"], "no_prohibited_claims_in_artifact_labels", True, _labels_are_safe(labels))
    synthesis["artifacts"] = {
        "figures": [_relative_or_posix(path, repo_root) for path in figure_paths],
        "tables": [_relative_or_posix(path, repo_root) for path in table_paths],
    }
    synthesis["overall_pass"] = all(item["pass"] for item in synthesis["checks"].values())
    write_json_report(synthesis, output_path)
    return synthesis


def _baseline_summary(report: dict[str, Any]) -> dict[str, Any]:
    metrics = _metrics_from_report(report.get("derived_locomotion_metrics", {}))
    return {
        "source_experiment_id": report.get("experiment_id"),
        "source_git_commit": report.get("git_commit"),
        "environment": {
            "python_version": report.get("python_version"),
            "flygym_version": report.get("flygym_version"),
            "mujoco_version": report.get("mujoco_version"),
        },
        "simulation": report.get("simulation_summary", {}),
        "actuation": report.get("actuator_summary", {}),
        "metrics": metrics,
    }


def _e1_summary(report: dict[str, Any]) -> dict[str, Any]:
    families: dict[str, Any] = {}
    for family, curve in report.get("response_curves", {}).items():
        families[family] = {
            "parameter_name": curve.get("parameter_name"),
            "perturbation_type": curve.get("perturbation_type"),
            "condition_order": curve.get("condition_order", []),
            "metrics": curve.get("metrics", {}),
        }
    return {
        "source_experiment_id": report.get("experiment_id"),
        "source_git_commit": report.get("git_commit"),
        "families": families,
    }


def _e2_summary(report: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for condition in report.get("conditions", []):
        scalars = condition.get("comparison", {}).get("scalars", {})
        row: dict[str, Any] = {
            "condition_id": condition.get("condition_id"),
            "category": condition.get("category"),
            "motor_scale": condition.get("motor_scale"),
            "coupling_scale": condition.get("coupling_scale"),
            "status": condition.get("status"),
            "overall_pass": condition.get("overall_pass"),
        }
        for metric in METRIC_KEYS:
            value = scalars.get(metric, {}).get("perturbed")
            if value is None and metric == "body_height_range_mm":
                value = scalars.get(metric, {}).get("perturbed")
            row[metric] = value
            row[f"{metric}_relative_delta"] = scalars.get(metric, {}).get("relative_delta")
        rows.append(row)
    return {
        "source_experiment_id": report.get("experiment_id"),
        "source_git_commit": report.get("git_commit"),
        "condition_summary": rows,
        "interaction_analysis": report.get("interaction_analysis", {}),
        "interpretation_boundary": "Simulation response surfaces only; no disease severity or biological calibration is assigned.",
    }


def _e3_summary(report: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for pair in report.get("pairs", []):
        row: dict[str, Any] = {
            "seed": pair.get("seed"),
            "status": pair.get("status"),
            "overall_pass": pair.get("overall_pass"),
            "same_seed_within_pair": pair.get("same_seed_within_pair"),
        }
        for metric in METRIC_KEYS:
            values = pair.get("key_metrics", {}).get(metric, {})
            row[f"baseline_{metric}"] = values.get("baseline")
            row[f"candidate_{metric}"] = values.get("candidate")
            row[f"delta_{metric}"] = values.get("absolute_delta")
        rows.append(row)
    return {
        "source_experiment_id": report.get("experiment_id"),
        "source_git_commit": report.get("git_commit"),
        "classification": report.get("robustness_assessment", {}).get("classification"),
        "seeds": [row.get("seed") for row in rows],
        "duration_s": report.get("validation_config", {}).get("validation_design", {}).get("duration_s"),
        "aggregate_statistics": report.get("aggregate_statistics", {}),
        "seed_summary": rows,
    }


def _e4_summary(report: dict[str, Any]) -> dict[str, Any]:
    assessments = report.get("concordance_assessments", [])
    classifications: dict[str, int] = {}
    for item in assessments:
        label = item.get("classification")
        classifications[label] = classifications.get(label, 0) + 1
    return {
        "source_experiment_id": report.get("experiment_id"),
        "source_git_commit": report.get("git_commit"),
        "overall_status": report.get("overall_scientific_status", {}),
        "classification_counts": classifications,
        "endpoint_mappings": report.get("endpoint_mappings", []),
        "concordance_assessments": assessments,
        "candidate": report.get("e3_simulation_phenotype", {}).get("frozen_candidate", {}),
        "interpretation_boundary": "Qualitative directional concordance only; unsupported endpoints remain unsupported.",
    }


def _e5_summary(report: dict[str, Any]) -> dict[str, Any]:
    assessments = report.get("condition_assessments", {})
    order = [
        "control",
        "impaired_candidate",
        "motor_partial_rescue",
        "coordination_partial_rescue",
        "combined_partial_rescue",
        "full_computational_restoration_reference",
    ]
    design = report.get("preregistered_design", {})
    impaired_design = design.get("frozen_impaired_candidate", {})
    condition_values: dict[str, dict[str, float | None]] = {
        "control": {},
        "impaired_candidate": {},
    }
    for endpoint in PRIMARY_METRICS:
        source = next(iter(assessments.values()))["primary_endpoints"][endpoint]
        condition_values["control"][endpoint] = source["control"]["mean"]
        condition_values["impaired_candidate"][endpoint] = source["impaired"]["mean"]
    for condition_id, assessment in assessments.items():
        for endpoint in PRIMARY_METRICS:
            condition_values.setdefault(condition_id, {})[endpoint] = assessment["primary_endpoints"][endpoint]["rescue"]["mean"]
    labels = {
        "control": "control",
        "impaired_candidate": "frozen candidate",
        "motor_partial_rescue": "motor partial restoration",
        "coordination_partial_rescue": "coordination partial restoration",
        "combined_partial_rescue": "combined partial restoration",
        "full_computational_restoration_reference": "full restoration reference",
    }
    rows: list[dict[str, Any]] = []
    for condition_id in order:
        if condition_id in ("control", "impaired_candidate"):
            design_state = (
                design.get("control", {})
                if condition_id == "control"
                else impaired_design
            )
            motor = design_state.get("motor_scale")
            coupling = design_state.get("coupling_scale")
            category = condition_id
            classification = "REFERENCE"
        else:
            item = assessments[condition_id]
            motor = item.get("motor_scale")
            coupling = item.get("coupling_scale")
            category = item.get("category")
            classification = item.get("classification") or "REFERENCE"
        for endpoint in PRIMARY_METRICS:
            values = assessments.get(condition_id, {}).get("primary_endpoints", {}).get(endpoint, {})
            rows.append(
                {
                    "condition_id": condition_id,
                    "condition_label": labels[condition_id],
                    "category": category,
                    "motor_scale": motor,
                    "coupling_scale": coupling,
                    "classification": classification,
                    "endpoint": endpoint,
                    "control_mean": values.get("control", {}).get("mean"),
                    "impaired_mean": values.get("impaired", {}).get("mean"),
                    "condition_mean": condition_values[condition_id].get(endpoint),
                    "aggregate_recovery_fraction": values.get("aggregate_recovery_fraction"),
                    "direction_toward_control_count": values.get("per_seed_direction_toward_control_count"),
                    "no_farther_count": values.get("per_seed_no_farther_from_control_count"),
                }
            )
    return {
        "source_experiment_id": report.get("experiment_id"),
        "source_git_commit": report.get("git_commit"),
        "condition_order": order,
        "condition_labels": [labels[item] for item in order],
        "endpoint_means": {
            endpoint: {condition: condition_values[condition].get(endpoint) for condition in order}
            for endpoint in PRIMARY_METRICS
        },
        "condition_summary": rows,
        "classification_summary": {
            condition: (assessments.get(condition, {}).get("classification") or "REFERENCE")
            for condition in assessments
        },
        "preregistered_design": design,
        "interpretation_boundary": "Computational reversibility only; not biological rescue or treatment response.",
    }


def _metrics_from_report(metrics: dict[str, Any]) -> dict[str, Any]:
    height = metrics.get("body_height_mm", {})
    action = metrics.get("controller_action_summary", {}).get("joint_angle_action_abs", {})
    return {
        "planar_displacement_mm": metrics.get("planar_displacement_mm"),
        "mean_planar_speed_mm_s": metrics.get("mean_planar_speed_mm_s"),
        "planar_path_length_mm": metrics.get("planar_path_length_mm"),
        "trajectory_efficiency": metrics.get("trajectory_efficiency"),
        "heading_yaw_change_rad": metrics.get("heading_yaw_change_rad"),
        "body_height_mean_mm": height.get("mean"),
        "body_height_min_mm": height.get("min"),
        "body_height_range_mm": _difference(height.get("max"), height.get("min")),
        "joint_angle_action_abs_mean": action.get("mean"),
        "observations_are_finite": metrics.get("observations_are_finite"),
        "derived_metrics_are_finite": metrics.get("derived_metrics_are_finite"),
    }


def _e1_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, family_data in summary["families"].items():
        metric_points = family_data.get("metrics", {})
        condition_ids = family_data.get("condition_order", [])
        for condition_id in condition_ids:
            row = {
                "family": family,
                "parameter_name": family_data.get("parameter_name"),
                "perturbation_type": family_data.get("perturbation_type"),
                "condition_id": condition_id,
            }
            for metric in METRIC_KEYS:
                point = next(
                    (item for item in metric_points.get(metric, {}).get("points", []) if item.get("condition_id") == condition_id),
                    {},
                )
                row[metric] = point.get("metric_value")
                row[f"{metric}_relative_delta"] = point.get("relative_delta")
            first_metric = metric_points.get("mean_planar_speed_mm_s", {}).get("points", [])
            point = next((item for item in first_metric if item.get("condition_id") == condition_id), {})
            row["parameter_value"] = point.get("parameter_value")
            rows.append(row)
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _artifact_labels() -> list[str]:
    return [
        "E1 computational proxy response curves",
        "E2 combined computational condition comparison",
        "E3 paired multi-seed computational robustness",
        "E5 computational reversibility endpoints",
    ]


def _labels_are_safe(labels: Iterable[str]) -> bool:
    return not any(
        term in label.lower()
        for label in labels
        for term in PROHIBITED_ARTIFACT_TERMS
    )


def _resolve_artifact_dir(configured: str, repo_root: str | Path) -> Path:
    path = Path(configured)
    return path if path.is_absolute() else Path(repo_root) / path


def _relative_or_posix(path: str | Path, repo_root: str | Path) -> str:
    try:
        return Path(path).resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return Path(path).as_posix()


def _candidate_pair(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "motor_scale": value.get("motor_scale"),
        "coupling_scale": value.get("coupling_scale"),
    }


def _all_checks_pass(report: dict[str, Any]) -> bool:
    checks = report.get("checks")
    return isinstance(checks, dict) and bool(checks) and all(
        isinstance(item, dict) and item.get("pass") is True
        for item in checks.values()
    )


def _all_condition_reports_pass(items: list[dict[str, Any]]) -> bool:
    return bool(items) and all(
        item.get("status") == "completed" and item.get("overall_pass") is True
        for item in items
    )


def _git_worktree_dirty(repo_root: str | Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return bool(result.stdout.strip())


def _add_check(
    checks: dict[str, dict[str, Any]], name: str, expected: Any, observed: Any
) -> None:
    checks[name] = {"expected": expected, "observed": observed, "pass": observed == expected}


def _required_text(mapping: Any, key: str) -> str:
    if not isinstance(mapping, dict):
        raise EvidenceValidationError(f"{key} must be read from a mapping.")
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise EvidenceValidationError(f"{key} must be a non-empty string.")
    return value.strip()


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _finite_float(value: Any, name: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise EvidenceValidationError(f"{name} must be numeric.") from exc
    if not math.isfinite(result):
        raise EvidenceValidationError(f"{name} must be finite.")
    return result


def _difference(first: Any, second: Any) -> float | None:
    if first is None or second is None:
        return None
    try:
        result = float(first) - float(second)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


__all__ = [
    "EvidenceSynthesisConfig",
    "EvidenceValidationError",
    "build_synthesis",
    "generate_figures",
    "generate_tables",
    "load_evidence_reports",
    "load_synthesis_config",
    "run_evidence_synthesis",
    "validate_frozen_evidence",
]
