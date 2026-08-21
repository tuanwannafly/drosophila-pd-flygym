"""Literature-grounded phenotype concordance reporting for Milestone E4."""

from __future__ import annotations

from datetime import UTC, datetime
import json
import math
from pathlib import Path
from typing import Any

import yaml

from drosophila_pd.anatomy.audit import git_commit
from drosophila_pd.experiments.candidate_robustness import (
    FROZEN_CANDIDATE_COUPLING_SCALE,
    FROZEN_CANDIDATE_MOTOR_SCALE,
)


CONCORDANCE_LABELS = {
    "CONCORDANT",
    "DISCORDANT",
    "NOT_COMPARABLE",
    "INSUFFICIENT_EVIDENCE",
}

OVERALL_STATUS_LABELS = {
    "PARTIAL_PHENOTYPE_CONCORDANCE",
    "INSUFFICIENT_CONCORDANCE",
    "DISCORDANT",
}

COMPARABILITY_LABELS = {
    "HIGH_QUALITATIVE",
    "MODERATE_QUALITATIVE",
    "LOW_QUALITATIVE",
    "NOT_COMPARABLE",
    "NOT_AVAILABLE",
    "UNSUPPORTED_FOR_PD_INTERPRETATION",
}

ALLOWED_COMPARISON_BASES = {
    "direction_only",
    "not_comparable",
    "unsupported_endpoint",
}

E3_REQUIRED_METRICS = (
    "mean_planar_speed_mm_s",
    "planar_displacement_mm",
    "planar_path_length_mm",
    "trajectory_efficiency",
    "heading_yaw_abs_change_rad",
    "body_height_mean_mm",
    "joint_angle_action_abs_mean",
)

SCIENTIFIC_SCOPE = (
    "Milestone E4 records qualitative phenotype concordance between the frozen "
    "E3 computational candidate and selected peer-reviewed Drosophila walking "
    "findings. It does not validate a Parkinson's disease model, tune "
    "parameters, infer dopamine depletion, or claim mechanistic equivalence."
)


def load_e4_evidence_matrix(path: str | Path) -> dict[str, Any]:
    """Load the curated E4 evidence matrix."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("E4 evidence matrix root must be a mapping.")
    return loaded


def load_json_report(path: str | Path) -> dict[str, Any]:
    """Load a JSON report."""

    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("JSON report root must be a mapping.")
    return loaded


def build_milestone_e4_concordance_report(
    *,
    matrix_path: str | Path,
    e3_evidence_path: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a JSON-serializable E4 concordance report."""

    matrix_path = Path(matrix_path)
    matrix = load_e4_evidence_matrix(matrix_path)
    if e3_evidence_path is None:
        configured_path = _require_mapping(
            matrix, "frozen_e3_evidence"
        ).get("path")
        e3_evidence_path = _resolve_repo_path(configured_path, repo_root=repo_root)
    e3_report = load_json_report(e3_evidence_path)
    e3_summary = build_e3_simulation_phenotype(e3_report)
    assessments = list(matrix.get("concordance_assessments") or [])
    overall_status = classify_overall_scientific_status(
        assessments=assessments,
        e3_summary=e3_summary,
    )
    checks = build_e4_checks(
        matrix=matrix,
        e3_report=e3_report,
        e3_summary=e3_summary,
        assessments=assessments,
        overall_status=overall_status,
    )
    return {
        "experiment_id": "milestone_e4_literature_grounded_concordance",
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "source_evidence": {
            "matrix_path": _display_path(matrix_path, repo_root=repo_root),
            "e3_evidence_path": _display_path(e3_evidence_path, repo_root=repo_root),
        },
        "literature_evidence": matrix.get("literature_evidence", []),
        "evidence_separation": matrix.get("evidence_separation", {}),
        "endpoint_mappings": matrix.get("endpoint_mappings", []),
        "e3_simulation_phenotype": e3_summary,
        "concordance_assessments": assessments,
        "unsupported_comparisons": build_unsupported_comparisons(matrix),
        "overall_scientific_status": overall_status,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_e3_simulation_phenotype(e3_report: dict[str, Any]) -> dict[str, Any]:
    """Extract the frozen E3 phenotype fields needed for E4."""

    metrics = _require_mapping(
        _require_mapping(e3_report, "aggregate_statistics"), "metrics"
    )
    sign_consistency = _require_mapping(e3_report, "sign_consistency")
    candidate = _require_mapping(e3_report, "frozen_candidate_definition")
    return {
        "source_experiment_id": e3_report.get("experiment_id"),
        "source_git_commit": e3_report.get("git_commit"),
        "source_overall_pass": e3_report.get("overall_pass"),
        "robustness_classification": _require_mapping(
            e3_report, "robustness_assessment"
        ).get("classification"),
        "duration_s": _require_mapping(e3_report, "paired_execution").get(
            "duration_s"
        ),
        "seeds": _require_mapping(e3_report, "paired_execution").get("seeds"),
        "frozen_candidate": {
            "motor_scale": candidate.get("motor_scale"),
            "coupling_scale": candidate.get("coupling_scale"),
            "selected_before_e3_execution": candidate.get(
                "selected_before_e3_execution"
            ),
            "post_hoc_tuning_permitted": candidate.get(
                "post_hoc_tuning_permitted"
            ),
        },
        "metrics": {
            metric: _aggregate_metric_summary(metrics, metric)
            for metric in E3_REQUIRED_METRICS
        },
        "sign_consistency": sign_consistency,
        "qualitative_summary": _e3_qualitative_summary(metrics, sign_consistency),
        "interpretation_boundary": (
            "These are simulation metrics from the frozen E3 candidate only; "
            "they are not biological measurements."
        ),
    }


def classify_overall_scientific_status(
    *,
    assessments: list[dict[str, Any]],
    e3_summary: dict[str, Any],
) -> dict[str, Any]:
    """Classify overall E4 concordance without creating a numeric disease score."""

    by_endpoint = {
        assessment.get("literature_endpoint"): assessment
        for assessment in assessments
    }
    speed_ok = (
        _assessment_label(by_endpoint, "walking_speed") == "CONCORDANT"
        and _metric_decreased(e3_summary, "mean_planar_speed_mm_s")
    )
    distance_ok = (
        _assessment_label(by_endpoint, "covered_distance") == "CONCORDANT"
        and _metric_decreased(e3_summary, "planar_path_length_mm")
        and _metric_decreased(e3_summary, "planar_displacement_mm")
    )
    unsupported_preserved = (
        _assessment_label(by_endpoint, "angular_velocity") == "NOT_COMPARABLE"
        and _assessment_label(by_endpoint, "thorax_or_body_height")
        == "INSUFFICIENT_EVIDENCE"
    )
    if speed_ok and distance_ok and unsupported_preserved:
        label = "PARTIAL_PHENOTYPE_CONCORDANCE"
        reason = (
            "Major adult walking speed and distance directions agree "
            "qualitatively with the selected literature, while unsupported "
            "endpoints remain explicitly limited."
        )
    elif any(
        assessment.get("classification") == "DISCORDANT"
        for assessment in assessments
    ):
        label = "DISCORDANT"
        reason = "At least one curated endpoint is marked discordant."
    else:
        label = "INSUFFICIENT_CONCORDANCE"
        reason = (
            "The curated evidence is insufficient to support partial phenotype "
            "concordance."
        )
    return {
        "label": label,
        "reason": reason,
        "score_created": False,
        "scope": (
            "Directional qualitative phenotype concordance only; not "
            "Parkinson's disease validation."
        ),
    }


def build_e4_checks(
    *,
    matrix: dict[str, Any],
    e3_report: dict[str, Any],
    e3_summary: dict[str, Any],
    assessments: list[dict[str, Any]],
    overall_status: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """Build E4 PASS/FAIL checks for schema and scientific boundaries."""

    return {
        "e3_report_passed": _check(True, e3_report.get("overall_pass")),
        "e3_robustness_classification": _check(
            "ROBUST", e3_summary.get("robustness_classification")
        ),
        "frozen_candidate_motor_scale": _check(
            FROZEN_CANDIDATE_MOTOR_SCALE,
            e3_summary["frozen_candidate"].get("motor_scale"),
        ),
        "frozen_candidate_coupling_scale": _check(
            FROZEN_CANDIDATE_COUPLING_SCALE,
            e3_summary["frozen_candidate"].get("coupling_scale"),
        ),
        "matrix_candidate_matches_e3": _check(
            True, _matrix_candidate_matches_e3(matrix, e3_summary)
        ),
        "post_hoc_tuning_forbidden": _check(
            False, e3_summary["frozen_candidate"].get("post_hoc_tuning_permitted")
        ),
        "no_parameter_tuning_in_e4": _check(
            True,
            _require_mapping(matrix, "frozen_e3_evidence").get(
                "no_parameter_tuning_in_e4"
            ),
        ),
        "valid_concordance_labels": _check(
            True, _valid_concordance_labels(matrix, assessments)
        ),
        "valid_endpoint_mappings": _check(True, _valid_endpoint_mappings(matrix)),
        "adult_larval_evidence_separated": _check(
            True, _adult_larval_evidence_separated(matrix)
        ),
        "direct_numeric_calibration_not_used": _check(
            True, _direct_numeric_calibration_not_used(matrix, assessments)
        ),
        "speed_direction_concordant": _check(
            True,
            _has_classification(
                assessments, "walking_speed", "CONCORDANT"
            )
            and _metric_decreased(e3_summary, "mean_planar_speed_mm_s"),
        ),
        "distance_direction_concordant": _check(
            True,
            _has_classification(
                assessments, "covered_distance", "CONCORDANT"
            )
            and _metric_decreased(e3_summary, "planar_path_length_mm")
            and _metric_decreased(e3_summary, "planar_displacement_mm"),
        ),
        "angular_velocity_not_forced": _check(
            True,
            _has_classification(
                assessments, "angular_velocity", "NOT_COMPARABLE"
            ),
        ),
        "body_height_not_interpreted_as_pd": _check(
            True,
            _has_classification(
                assessments, "thorax_or_body_height", "INSUFFICIENT_EVIDENCE"
            ),
        ),
        "overall_status_allowed": _check(
            True, overall_status.get("label") in OVERALL_STATUS_LABELS
        ),
        "no_weighted_pd_score": _check(False, overall_status.get("score_created")),
        "scientific_scope_preserved": _check(
            True, "does not validate" in matrix.get("scientific_scope", "")
        ),
    }


def build_unsupported_comparisons(matrix: dict[str, Any]) -> list[dict[str, Any]]:
    """Return endpoint mappings that must not be interpreted as concordant."""

    unsupported = []
    for mapping in matrix.get("endpoint_mappings", []) or []:
        comparability = mapping.get("comparability")
        if comparability in {
            "LOW_QUALITATIVE",
            "NOT_COMPARABLE",
            "NOT_AVAILABLE",
            "UNSUPPORTED_FOR_PD_INTERPRETATION",
        }:
            unsupported.append(
                {
                    "literature_endpoint": mapping.get("literature_endpoint"),
                    "simulation_metric": mapping.get("simulation_metric"),
                    "comparability": comparability,
                    "rationale": mapping.get("rationale"),
                }
            )
    return unsupported


def _aggregate_metric_summary(
    metrics: dict[str, Any], metric: str
) -> dict[str, Any]:
    data = _require_mapping(metrics, metric)
    baseline = _require_mapping(data, "baseline")
    candidate = _require_mapping(data, "candidate")
    absolute_delta = _require_mapping(data, "absolute_delta")
    relative_delta = _require_mapping(data, "relative_delta")
    return {
        "baseline_mean": baseline.get("mean"),
        "candidate_mean": candidate.get("mean"),
        "absolute_delta_mean": absolute_delta.get("mean"),
        "relative_delta_mean": relative_delta.get("mean"),
        "relative_delta_percent_mean": _percent(relative_delta.get("mean")),
        "count": baseline.get("count"),
    }


def _e3_qualitative_summary(
    metrics: dict[str, Any], sign_consistency: dict[str, Any]
) -> dict[str, Any]:
    return {
        "mean_speed": _direction_summary(
            metrics, "mean_planar_speed_mm_s"
        ),
        "planar_displacement": _direction_summary(
            metrics, "planar_displacement_mm"
        ),
        "planar_path_length": _direction_summary(
            metrics, "planar_path_length_mm"
        ),
        "trajectory_efficiency": _direction_summary(
            metrics, "trajectory_efficiency"
        ),
        "body_height_mean": _direction_summary(metrics, "body_height_mean_mm"),
        "absolute_yaw_change": _direction_summary(
            metrics, "heading_yaw_abs_change_rad"
        ),
        "speed_delta_negative_seed_count": sign_consistency.get(
            "number_of_seeds_negative_speed_delta"
        ),
        "displacement_delta_negative_seed_count": sign_consistency.get(
            "number_of_seeds_negative_displacement_delta"
        ),
        "yaw_abs_change_positive_seed_count": sign_consistency.get(
            "number_of_seeds_positive_yaw_abs_change_delta"
        ),
        "trajectory_efficiency_negative_seed_count": sign_consistency.get(
            "number_of_seeds_negative_trajectory_efficiency_delta"
        ),
    }


def _direction_summary(metrics: dict[str, Any], metric: str) -> str:
    data = _require_mapping(metrics, metric)
    delta = _finite_or_none(
        _require_mapping(data, "absolute_delta").get("mean")
    )
    if delta is None:
        return "unavailable"
    if delta < 0:
        return "decreased"
    if delta > 0:
        return "increased"
    return "unchanged"


def _valid_concordance_labels(
    matrix: dict[str, Any], assessments: list[dict[str, Any]]
) -> bool:
    policy = _require_mapping(matrix, "classification_policy")
    policy_labels = set(policy.get("allowed_concordance_labels") or [])
    if policy_labels != CONCORDANCE_LABELS:
        return False
    if set(policy.get("allowed_overall_status_labels") or []) != OVERALL_STATUS_LABELS:
        return False
    return all(
        assessment.get("classification") in CONCORDANCE_LABELS
        for assessment in assessments
    )


def _valid_endpoint_mappings(matrix: dict[str, Any]) -> bool:
    mappings = matrix.get("endpoint_mappings")
    if not isinstance(mappings, list) or not mappings:
        return False
    for mapping in mappings:
        if not isinstance(mapping, dict):
            return False
        if not mapping.get("literature_endpoint"):
            return False
        if mapping.get("comparability") not in COMPARABILITY_LABELS:
            return False
        if mapping.get("direct_numeric_calibration_permitted") is not False:
            return False
        if mapping.get("simulation_metric") in (None, ""):
            return False
    return True


def _adult_larval_evidence_separated(matrix: dict[str, Any]) -> bool:
    separation = _require_mapping(matrix, "evidence_separation")
    adult_ids = separation.get("adult_evidence_ids")
    larval_ids = separation.get("larval_or_non_adult_evidence_ids")
    evidence_ids = {
        item.get("evidence_id")
        for item in matrix.get("literature_evidence", []) or []
    }
    return (
        isinstance(adult_ids, list)
        and len(adult_ids) >= 2
        and set(adult_ids).issubset(evidence_ids)
        and isinstance(larval_ids, list)
    )


def _direct_numeric_calibration_not_used(
    matrix: dict[str, Any], assessments: list[dict[str, Any]]
) -> bool:
    policy = _require_mapping(matrix, "classification_policy")
    if policy.get("direct_numeric_calibration_allowed") is not False:
        return False
    if policy.get("qualitative_direction_only") is not True:
        return False
    for assessment in assessments:
        if assessment.get("direct_numeric_calibration_used") is not False:
            return False
        if assessment.get("comparison_basis") not in ALLOWED_COMPARISON_BASES:
            return False
    return True


def _matrix_candidate_matches_e3(
    matrix: dict[str, Any], e3_summary: dict[str, Any]
) -> bool:
    matrix_candidate = _require_mapping(
        _require_mapping(matrix, "frozen_e3_evidence"), "candidate"
    )
    e3_candidate = _require_mapping(e3_summary, "frozen_candidate")
    return (
        math.isclose(
            float(matrix_candidate.get("motor_scale")),
            float(e3_candidate.get("motor_scale")),
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        and math.isclose(
            float(matrix_candidate.get("coupling_scale")),
            float(e3_candidate.get("coupling_scale")),
            rel_tol=0.0,
            abs_tol=1e-12,
        )
        and matrix_candidate.get("selected_before_e3_execution")
        == e3_candidate.get("selected_before_e3_execution")
        and matrix_candidate.get("post_hoc_tuning_permitted")
        == e3_candidate.get("post_hoc_tuning_permitted")
    )


def _metric_decreased(e3_summary: dict[str, Any], metric: str) -> bool:
    data = _require_mapping(_require_mapping(e3_summary, "metrics"), metric)
    return (
        _finite_or_none(data.get("candidate_mean")) is not None
        and _finite_or_none(data.get("baseline_mean")) is not None
        and float(data["candidate_mean"]) < float(data["baseline_mean"])
        and _finite_or_none(data.get("absolute_delta_mean")) is not None
        and float(data["absolute_delta_mean"]) < 0
    )


def _assessment_label(
    by_endpoint: dict[str, dict[str, Any]], endpoint: str
) -> str | None:
    assessment = by_endpoint.get(endpoint)
    if assessment is None:
        return None
    return assessment.get("classification")


def _has_classification(
    assessments: list[dict[str, Any]], endpoint: str, label: str
) -> bool:
    return any(
        item.get("literature_endpoint") == endpoint
        and item.get("classification") == label
        for item in assessments
    )


def _resolve_repo_path(value: Any, *, repo_root: str | Path | None) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Configured path must be a non-empty string.")
    path = Path(value)
    if path.is_absolute():
        return path
    return Path(repo_root or Path.cwd()) / path


def _display_path(path: str | Path, *, repo_root: str | Path | None) -> str:
    path = Path(path)
    if repo_root is None:
        return str(path)
    try:
        return path.resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return str(path)


def _require_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be a mapping.")
    return value


def _finite_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _percent(value: Any) -> float | None:
    finite = _finite_or_none(value)
    if finite is None:
        return None
    return finite * 100.0


def _check(expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


__all__ = [
    "ALLOWED_COMPARISON_BASES",
    "COMPARABILITY_LABELS",
    "CONCORDANCE_LABELS",
    "E3_REQUIRED_METRICS",
    "OVERALL_STATUS_LABELS",
    "SCIENTIFIC_SCOPE",
    "build_e3_simulation_phenotype",
    "build_e4_checks",
    "build_milestone_e4_concordance_report",
    "build_unsupported_comparisons",
    "classify_overall_scientific_status",
    "load_e4_evidence_matrix",
    "load_json_report",
]
