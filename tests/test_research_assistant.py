"""Contracts for the model-free research assistant orchestration layer."""

import json
import math

from drosophila_pd.research_assistant import ResearchAssistant


def complete_artifacts() -> dict:
    return {
        "dataset": {"name": "observed-rollout"},
        "analysis": {"velocity": [1.0, 2.0]},
        "statistics": {"mean_velocity": 1.5},
        "validation": {"overall_pass": True},
        "reports": {"report": "existing"},
    }


def test_assistant_reads_existing_artifacts_and_reports_scope() -> None:
    artifacts = complete_artifacts()
    report = ResearchAssistant(artifacts=artifacts).generate()

    assert report.summary["available_artifacts"] == 5
    assert report.summary["validation_status"] == "PASS"
    assert not report.warnings
    assert "biological" in report.scientific_scope
    assert artifacts == complete_artifacts()


def test_assistant_reports_missing_artifacts_and_validation_failure() -> None:
    report = ResearchAssistant(artifacts={"validation": {"overall_pass": False}}).generate()

    assert report.summary["validation_status"] == "FAIL"
    assert "validation.overall_pass is false" in report.warnings
    assert any(item.startswith("Missing dataset") for item in report.warnings)


def test_assistant_detects_nonfinite_values_without_analysis() -> None:
    assistant = ResearchAssistant(artifacts={"analysis": {"speed": [math.nan]}})

    assert assistant.detect_anomalies() == ["non-finite value at root.analysis.speed[0]"]


def test_explanations_and_file_output(tmp_path) -> None:
    assistant = ResearchAssistant(artifacts=complete_artifacts())
    assert "velocity" in assistant.explain_metric("Velocity")
    assert "position" in assistant.explain_chart("trajectory")
    assert "pass" in assistant.explain_validation({"overall_pass": True})

    paths = assistant.write(tmp_path)
    assert set(paths) == {"json", "markdown"}
    payload = json.loads(paths["json"].read_text(encoding="utf-8"))
    assert payload["assistant_version"] == 1
    assert "Scientific Scope" in paths["markdown"].read_text(encoding="utf-8")


def test_assistant_can_materialize_json_path(tmp_path) -> None:
    source = tmp_path / "analysis.json"
    source.write_text('{"velocity": [1]}', encoding="utf-8")

    assistant = ResearchAssistant(artifacts={"analysis": source})

    assert assistant.read_artifacts()["analysis"] == {"velocity": [1]}
