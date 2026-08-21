from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import json
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.analysis.evidence_synthesis import (  # noqa: E402
    EvidenceValidationError,
    build_synthesis,
    generate_figures,
    generate_tables,
    load_evidence_reports,
    load_synthesis_config,
    run_evidence_synthesis,
    validate_frozen_evidence,
)


def test_frozen_evidence_loads_and_candidate_is_consistent():
    config = load_synthesis_config(REPO_ROOT / "configs/analysis/milestone_e6.yaml")
    reports, manifest = load_evidence_reports(config, repo_root=REPO_ROOT)
    checks = validate_frozen_evidence(reports, config=config)
    synthesis = build_synthesis(
        reports,
        manifest,
        config=config,
        repo_root=REPO_ROOT,
        validation_checks=checks,
    )

    assert len(manifest) == 8
    assert synthesis["overall_pass"] is True
    assert synthesis["frozen_candidate_definition"] == {
        "motor_scale": 0.8,
        "coupling_scale": 0.75,
        "selection_basis": "Frozen E2/E3 computational candidate; no E6 tuning.",
    }
    assert synthesis["e3_robustness_summary"]["classification"] == "ROBUST"
    assert synthesis["e5_reversibility_summary"]["endpoint_means"][
        "mean_planar_speed_mm_s"
    ]["motor_partial_rescue"] == pytest.approx(12.798554263221726)


def test_missing_evidence_fails_clearly(tmp_path):
    config = load_synthesis_config(REPO_ROOT / "configs/analysis/milestone_e6.yaml")
    paths = dict(config.required_evidence)
    paths["e5"] = str(tmp_path / "missing.json")
    missing_config = replace(config, required_evidence=paths)

    with pytest.raises(EvidenceValidationError, match="missing evidence file"):
        load_evidence_reports(missing_config, repo_root=REPO_ROOT)


def test_failed_upstream_evidence_is_rejected():
    config = load_synthesis_config(REPO_ROOT / "configs/analysis/milestone_e6.yaml")
    reports, _ = load_evidence_reports(config, repo_root=REPO_ROOT)
    failed = deepcopy(reports)
    failed["e3"]["overall_pass"] = False

    with pytest.raises(EvidenceValidationError, match="e3_overall_pass"):
        validate_frozen_evidence(failed, config=config)


def test_frozen_candidate_mismatch_is_rejected():
    config = load_synthesis_config(REPO_ROOT / "configs/analysis/milestone_e6.yaml")
    reports, _ = load_evidence_reports(config, repo_root=REPO_ROOT)
    mismatched = deepcopy(reports)
    mismatched["e4"]["e3_simulation_phenotype"]["frozen_candidate"]["motor_scale"] = 0.7

    with pytest.raises(EvidenceValidationError, match="frozen_candidate_e4"):
        validate_frozen_evidence(mismatched, config=config)


def test_tables_and_figures_are_generated_from_report_data(tmp_path):
    config = load_synthesis_config(REPO_ROOT / "configs/analysis/milestone_e6.yaml")
    reports, manifest = load_evidence_reports(config, repo_root=REPO_ROOT)
    synthesis = build_synthesis(
        reports,
        manifest,
        config=config,
        repo_root=REPO_ROOT,
    )

    table_paths = generate_tables(synthesis, output_dir=tmp_path / "tables")
    figure_paths = generate_figures(synthesis, output_dir=tmp_path / "figures")

    assert len(table_paths) == 5
    assert len(figure_paths) == 4
    assert all(Path(path).is_file() for path in table_paths + figure_paths)
    assert "Parkinson" not in " ".join(synthesis["artifact_labels"])


def test_end_to_end_output_schema_without_flygym(tmp_path):
    config = load_synthesis_config(REPO_ROOT / "configs/analysis/milestone_e6.yaml")
    local_config = replace(
        config,
        figures_dir=str(tmp_path / "figures"),
        tables_dir=str(tmp_path / "tables"),
    )
    config_path = tmp_path / "config.yaml"
    config_data = {
        "experiment_id": local_config.experiment_id,
        "required_evidence": local_config.required_evidence,
        "frozen_candidate": {
            "motor_scale": local_config.frozen_motor_scale,
            "coupling_scale": local_config.frozen_coupling_scale,
        },
        "artifacts": {
            "figures_dir": local_config.figures_dir,
            "tables_dir": local_config.tables_dir,
        },
    }
    import yaml

    config_path.write_text(yaml.safe_dump(config_data), encoding="utf-8")
    output_path = tmp_path / "synthesis.json"
    report = run_evidence_synthesis(
        config_path=config_path,
        output_path=output_path,
        repo_root=REPO_ROOT,
    )

    saved = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["overall_pass"] is True
    assert saved["overall_pass"] is True
    assert set(saved) >= {
        "input_evidence_manifest",
        "frozen_candidate_definition",
        "e1_parameter_response_summary",
        "e2_interaction_summary",
        "e3_robustness_summary",
        "e4_concordance_summary",
        "e5_reversibility_summary",
        "scientific_synthesis",
        "checks",
    }
