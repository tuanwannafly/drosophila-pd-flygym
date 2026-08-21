"""End-to-end tests for the unified orchestration layer.

The fixture is a non-scientific metadata artifact; no rollout or evidence is
created by these tests.
"""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import zipfile

from drosophila_pd.research_pipeline import DatasetInput, StudyOrchestrator, StudyRequest
from drosophila_pd.digital_twin_platform import DigitalTwinPlatform


def test_unified_study_manifest_package_and_integrity(tmp_path: Path) -> None:
    source = tmp_path / "catalog_fixture.json"
    source.write_text('{"fixture": true, "scientific_data": false}\n', encoding="utf-8")
    request = StudyRequest(
        study_id="study_fixture",
        name="Orchestration Fixture",
        datasets=(DatasetInput(source=source, dataset_id="fixture_dataset"),),
        analysis_stage=lambda entries, output: {
            "available": True,
            "dataset_ids": [entry.dataset_id for entry in entries],
            "figure_records": [
                {
                    "condition": "fixture",
                    "arrays": {"thorax_positions": [[0.0, 0.0], [1.0, 0.1]]},
                    "metrics": {"mean_speed": 1.0, "exploration_index": 0.5},
                }
            ],
        },
        statistical_samples={"fixture_metric": [1.0, 1.1, 0.9]},
        digital_twin_platform=DigitalTwinPlatform(),
        metadata={"fixture_only": True},
    )
    orchestrator = StudyOrchestrator(tmp_path, tmp_path / "outputs")
    result = orchestrator.run(request)

    assert result.validation["overall_pass"] is True
    assert result.manifest_path.is_file()
    assert result.package_path.is_file()
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert {"datasets", "campaign", "digital_twins", "analysis", "statistics", "validation", "reports", "figures", "publication", "hashes", "provenance"} <= set(manifest)
    assert manifest["datasets"][0]["dataset_id"] == "fixture_dataset"
    assert manifest["analysis"]["available"] is True
    assert manifest["statistics"]["available"] is True
    assert manifest["publication"]["asset_count"] > 0

    with zipfile.ZipFile(result.package_path) as archive:
        names = set(archive.namelist())
    assert {"study.json", "README.md", "checksums/", "reports/", "validation/", "figures/", "tables/", "publication/", "artifacts/"} <= names
    assert "checksums/sha256.json" in names
    assert any(name.startswith("publication/results/") for name in names)

    source.write_text('{"fixture": changed}\n', encoding="utf-8")
    invalid = orchestrator.validate(request.study_id)
    assert invalid["overall_pass"] is False
    assert invalid["checks"]["datasets"]["overall_pass"] is False


def test_study_cli_smoke(tmp_path: Path) -> None:
    source = tmp_path / "input.json"
    source.write_text('{"fixture": true}\n', encoding="utf-8")
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_study.py"
    help_result = subprocess.run([sys.executable, str(script), "--help"], check=True, capture_output=True, text=True)
    assert "--dataset" in help_result.stdout
    run = subprocess.run(
        [
            sys.executable,
            str(script),
            "--study-id",
            "cli_fixture",
            "--name",
            "CLI Fixture",
            "--dataset",
            f"fixture={source}",
            "--output-root",
            str(tmp_path / "outputs"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(run.stdout)
    assert payload["overall_pass"] is True
    assert Path(payload["study"]).is_file()
    assert Path(payload["package"]).is_file()
