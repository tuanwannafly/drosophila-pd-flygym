from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.experiments.phenotype_concordance import (  # noqa: E402
    CONCORDANCE_LABELS,
    build_e3_simulation_phenotype,
    build_e4_checks,
    build_milestone_e4_concordance_report,
    build_unsupported_comparisons,
    classify_overall_scientific_status,
    load_e4_evidence_matrix,
    load_json_report,
)


MATRIX_PATH = REPO_ROOT / "docs" / "scientific" / "e4_evidence_matrix.yaml"
E3_EVIDENCE_PATH = (
    REPO_ROOT
    / "results"
    / "validation"
    / "milestone_e3_candidate_robustness.json"
)


def test_e4_matrix_records_primary_adult_citations_and_separates_larval_evidence():
    matrix = load_e4_evidence_matrix(MATRIX_PATH)

    adult_ids = matrix["evidence_separation"]["adult_evidence_ids"]
    larval_ids = matrix["evidence_separation"]["larval_or_non_adult_evidence_ids"]
    citations = {
        item["evidence_id"]: item["citation"]
        for item in matrix["literature_evidence"]
    }

    assert adult_ids == [
        "riemensperger_2011_adult_dopamine_deficiency_walking",
        "chen_2014_old_adult_a30p_walking",
    ]
    assert larval_ids == []
    assert citations[adult_ids[0]]["doi"] == "10.1073/pnas.1010930108"
    assert citations[adult_ids[0]]["pmid"] == "21187381"
    assert citations[adult_ids[1]]["doi"] == "10.1111/gbb.12172"
    assert citations[adult_ids[1]]["pmid"] == "25113870"


def test_e4_report_uses_frozen_e3_evidence_and_classifies_partial_concordance():
    report = build_milestone_e4_concordance_report(
        matrix_path=MATRIX_PATH,
        e3_evidence_path=E3_EVIDENCE_PATH,
        repo_root=REPO_ROOT,
    )

    metrics = report["e3_simulation_phenotype"]["metrics"]

    assert report["overall_pass"] is True
    assert report["overall_scientific_status"]["label"] == (
        "PARTIAL_PHENOTYPE_CONCORDANCE"
    )
    assert metrics["mean_planar_speed_mm_s"]["baseline_mean"] == (
        13.751281674590993
    )
    assert metrics["mean_planar_speed_mm_s"]["candidate_mean"] == (
        12.302040063313584
    )
    assert metrics["joint_angle_action_abs_mean"][
        "relative_delta_percent_mean"
    ] == -19.995156821323032
    assert report["e3_simulation_phenotype"]["frozen_candidate"] == {
        "motor_scale": 0.8,
        "coupling_scale": 0.75,
        "selected_before_e3_execution": True,
        "post_hoc_tuning_permitted": False,
    }
    assert "does not validate" in report["scientific_scope"]


def test_e4_labels_endpoint_mappings_and_unsupported_comparisons_are_explicit():
    matrix = load_e4_evidence_matrix(MATRIX_PATH)
    report = build_milestone_e4_concordance_report(
        matrix_path=MATRIX_PATH,
        e3_evidence_path=E3_EVIDENCE_PATH,
        repo_root=REPO_ROOT,
    )
    labels = {
        assessment["classification"]
        for assessment in report["concordance_assessments"]
    }
    unsupported = {
        item["literature_endpoint"]: item
        for item in build_unsupported_comparisons(matrix)
    }

    assert labels <= CONCORDANCE_LABELS
    assert report["checks"]["valid_endpoint_mappings"]["pass"] is True
    assert unsupported["angular_velocity"]["comparability"] == "LOW_QUALITATIVE"
    assert unsupported["distance_per_movement"]["comparability"] == "NOT_AVAILABLE"
    assert unsupported["thorax_or_body_height"]["comparability"] == (
        "UNSUPPORTED_FOR_PD_INTERPRETATION"
    )


def test_e4_rejects_direct_numeric_calibration_semantics():
    matrix = load_e4_evidence_matrix(MATRIX_PATH)
    e3_report = load_json_report(E3_EVIDENCE_PATH)
    e3_summary = build_e3_simulation_phenotype(e3_report)
    assessments = deepcopy(matrix["concordance_assessments"])
    assessments[0]["direct_numeric_calibration_used"] = True

    checks = build_e4_checks(
        matrix=matrix,
        e3_report=e3_report,
        e3_summary=e3_summary,
        assessments=assessments,
        overall_status=classify_overall_scientific_status(
            assessments=assessments,
            e3_summary=e3_summary,
        ),
    )

    assert checks["direct_numeric_calibration_not_used"]["pass"] is False


def test_e4_rejects_candidate_tuning_in_matrix():
    matrix = load_e4_evidence_matrix(MATRIX_PATH)
    matrix["frozen_e3_evidence"]["candidate"]["motor_scale"] = 0.7
    e3_report = load_json_report(E3_EVIDENCE_PATH)
    e3_summary = build_e3_simulation_phenotype(e3_report)

    checks = build_e4_checks(
        matrix=matrix,
        e3_report=e3_report,
        e3_summary=e3_summary,
        assessments=matrix["concordance_assessments"],
        overall_status=classify_overall_scientific_status(
            assessments=matrix["concordance_assessments"],
            e3_summary=e3_summary,
        ),
    )

    assert checks["matrix_candidate_matches_e3"]["pass"] is False


def test_e4_does_not_allow_yaw_change_to_be_forced_into_angular_velocity():
    matrix = load_e4_evidence_matrix(MATRIX_PATH)
    e3_report = load_json_report(E3_EVIDENCE_PATH)
    e3_summary = build_e3_simulation_phenotype(e3_report)
    assessments = deepcopy(matrix["concordance_assessments"])
    for assessment in assessments:
        if assessment["literature_endpoint"] == "angular_velocity":
            assessment["classification"] = "CONCORDANT"

    checks = build_e4_checks(
        matrix=matrix,
        e3_report=e3_report,
        e3_summary=e3_summary,
        assessments=assessments,
        overall_status=classify_overall_scientific_status(
            assessments=assessments,
            e3_summary=e3_summary,
        ),
    )

    assert checks["angular_velocity_not_forced"]["pass"] is False


def test_e4_overall_status_becomes_insufficient_without_major_distance_concordance():
    matrix = load_e4_evidence_matrix(MATRIX_PATH)
    e3_summary = build_e3_simulation_phenotype(load_json_report(E3_EVIDENCE_PATH))
    assessments = deepcopy(matrix["concordance_assessments"])
    for assessment in assessments:
        if assessment["literature_endpoint"] == "covered_distance":
            assessment["classification"] = "INSUFFICIENT_EVIDENCE"

    status = classify_overall_scientific_status(
        assessments=assessments,
        e3_summary=e3_summary,
    )

    assert status["label"] == "INSUFFICIENT_CONCORDANCE"
    assert status["score_created"] is False
