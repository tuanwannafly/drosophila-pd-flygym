"""Read-only FlyGym dataset adapter contracts.

Fixtures are structural metadata files only; they are not scientific evidence
and are never used by the simulation or analysis pipeline.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

from drosophila_pd.dataset_adapter import DatasetValidator, RolloutLocator, discover_datasets


def test_empty_dataset_roots_report_waiting_for_all_types(tmp_path: Path) -> None:
    report = discover_datasets((tmp_path / "datasets",))
    assert report.state == "WAITING_DATASET"
    assert report.datasets == []
    assert set(report.missing_types) == {"healthy", "pd", "candidate", "control", "validation", "benchmark"}


def test_manifest_discovery_is_ready_without_parsing_unlisted_payloads(tmp_path: Path) -> None:
    root = tmp_path / "datasets" / "healthy" / "1.0.0"
    root.mkdir(parents=True)
    payload = root / "rollouts" / "metadata.txt"
    payload.parent.mkdir()
    payload.write_text("fixture-only metadata artifact\n", encoding="utf-8")
    digest = hashlib.sha256(payload.read_bytes()).hexdigest()
    (root / "metadata.json").write_text(json.dumps({"fixture": True}), encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "dataset_id": "fixture_dataset",
                "dataset_type": "healthy",
                "dataset_version": "1.0.0",
                "status": "COMPLETE",
                "entries": [{"relative_path": "rollouts/metadata.txt", "sha256": digest, "byte_size": payload.stat().st_size}],
                "checksums": {"rollouts/metadata.txt": digest},
                "citation": "fixture",
                "scientific_scope": "fixture only",
            }
        ),
        encoding="utf-8",
    )
    report = discover_datasets((tmp_path / "datasets",))
    assert report.state == "READY"
    assert report.datasets[0].dataset_id == "fixture_dataset"
    assert report.datasets[0].rollout_files[0].observed_sha256 == digest
    assert not (root / "fixture_output.json").exists()


def test_validator_passes_structural_trajectory_fixture(tmp_path: Path) -> None:
    root = tmp_path / "datasets" / "healthy" / "1.0.0"
    (root / "rollouts").mkdir(parents=True)
    trajectory = root / "rollouts" / "trajectory.csv"
    trajectory.write_text("frame,x,y,z\n0,0,0,0\n1,1,0,0\n", encoding="utf-8")
    digest = hashlib.sha256(trajectory.read_bytes()).hexdigest()
    (root / "metadata.json").write_text(json.dumps({"fixture": True}), encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "dataset_id": "fixture_trajectory",
                "dataset_type": "healthy",
                "dataset_version": "1.0.0",
                "status": "VALIDATED",
                "source_commit": "0" * 40,
                "entries": [{"relative_path": "rollouts/trajectory.csv", "sha256": digest, "byte_size": trajectory.stat().st_size}],
                "checksums": {"rollouts/trajectory.csv": digest},
                "citation": "fixture",
                "scientific_scope": "fixture only",
            }
        ),
        encoding="utf-8",
    )
    dataset = discover_datasets((tmp_path / "datasets",)).datasets[0]
    result = DatasetValidator().validate(dataset)
    assert result.overall_pass is True
    assert result.checks["frame_counts"]["frame_counts"]["rollouts/trajectory.csv"] == 2


def test_locator_reports_missing_and_unsafe_manifest_entries(tmp_path: Path) -> None:
    records = RolloutLocator().locate(
        tmp_path,
        {"entries": [{"relative_path": "rollouts/missing.npz"}, {"relative_path": "../outside.npz"}]},
    )
    assert next(item for item in records if item.relative_path == "rollouts/missing.npz").exists is False
    invalid = next(item for item in records if item.relative_path == "../outside.npz")
    assert invalid.kind == "invalid"
    assert invalid.frame_count_error


def test_dataset_cli_commands_and_report_wait_without_payload(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "dataset_cli.py"
    for command in ("discover", "validate", "status", "summary"):
        completed = subprocess.run(
            [sys.executable, str(script), command, "--root", str(tmp_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(completed.stdout)["state"] == "WAITING_DATASET"
    output = tmp_path / "report"
    completed = subprocess.run(
        [sys.executable, str(script), "report", "--root", str(tmp_path), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["state"] == "WAITING_DATASET"
    assert (output / "dataset_report.json").is_file()
    assert (output / "dataset_report.md").is_file()
