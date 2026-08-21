"""Contract tests for the dataset-gated V6 execution layer."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from drosophila_pd.research_execution import (
    ArtifactRegistry,
    DatasetDiscovery,
    ExecutionContext,
    ExecutionHistory,
    ExecutionRuntime,
    ExecutionState,
)


def test_execution_state_machine_rejects_skipped_transitions() -> None:
    history = ExecutionHistory()
    history.transition(ExecutionState.READY)
    history.transition(ExecutionState.RUNNING)
    history.transition(ExecutionState.VALIDATING)
    history.transition(ExecutionState.EXPORTING)
    history.transition(ExecutionState.COMPLETED)
    assert history.state is ExecutionState.COMPLETED
    with pytest.raises(ValueError, match="invalid execution transition"):
        history.transition(ExecutionState.RUNNING)


def test_dataset_discovery_ignores_planning_template_and_does_not_parse_rollout(tmp_path: Path) -> None:
    planning = tmp_path / "research" / "campaigns" / "healthy_baseline"
    planning.mkdir(parents=True)
    (planning / "dataset_manifest.template.json").write_text(
        json.dumps({"status": "PLANNING_ONLY", "entries": []}), encoding="utf-8"
    )
    result = DatasetDiscovery().discover((tmp_path / "datasets", tmp_path / "research" / "datasets"))
    assert result.state is ExecutionState.WAITING_DATASET
    assert result.datasets == []
    assert result.as_dict()["rollout_parsing"] == "not performed"


def test_manifest_without_payload_is_waiting(tmp_path: Path) -> None:
    root = tmp_path / "datasets" / "healthy"
    root.mkdir(parents=True)
    (root / "manifest.json").write_text(
        json.dumps({"dataset_id": "healthy", "status": "READY", "entries": []}), encoding="utf-8"
    )
    result = DatasetDiscovery().discover((tmp_path / "datasets",))
    assert result.state is ExecutionState.WAITING_DATASET
    assert result.datasets[0].reason == "Manifest contains no payload entries."


def test_artifact_registry_registers_existing_files_and_verifies(tmp_path: Path) -> None:
    report = tmp_path / "reports" / "report.json"
    report.parent.mkdir()
    report.write_text("{}\n", encoding="utf-8")
    registry = ArtifactRegistry(tmp_path)
    record = registry.register(report, "reports")
    assert record.byte_size > 0
    assert registry.verify()["overall_pass"] is True
    with pytest.raises(FileNotFoundError):
        registry.register(tmp_path / "missing.json", "reports")
    with pytest.raises(ValueError, match="unsupported artifact category"):
        registry.register(report, "unknown")


def test_execute_waits_without_calling_downstream_pipeline(tmp_path: Path) -> None:
    called = False

    def fail_if_called(*_args: object) -> None:
        nonlocal called
        called = True
        raise AssertionError("downstream pipeline must not run without a dataset")

    context = ExecutionContext(tmp_path, output_root=tmp_path / "execution")
    result = ExecutionRuntime(context, study_runner=fail_if_called).execute()
    assert result.state is ExecutionState.WAITING_DATASET
    assert called is False
    assert (tmp_path / "execution" / "execution_report.json").is_file()
    assert (tmp_path / "execution" / "execution_report.md").is_file()
    payload = json.loads((tmp_path / "execution" / "execution_report.json").read_text(encoding="utf-8"))
    assert payload["state"] == "WAITING_DATASET"
    assert all(item["status"] == "WAITING_DATASET" for item in payload["stages"])


def test_cli_discover_reports_waiting_dataset(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "run_campaign.py"
    completed = subprocess.run(
        [sys.executable, str(script), "discover", "--root", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(completed.stdout)
    assert payload["state"] == "WAITING_DATASET"
    assert payload["rollout_parsing"] == "not performed"


def test_healthy_batch_executes_imported_npz_through_existing_pipeline(tmp_path: Path) -> None:
    dataset_root = tmp_path / "datasets" / "healthy" / "Healthy_001"
    rollout_path = dataset_root / "rollouts" / "rollout_arrays.npz"
    rollout_path.parent.mkdir(parents=True)
    positions = np.asarray([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [2.0, 0.5, 1.0]])
    quaternions = np.tile([1.0, 0.0, 0.0, 0.0], (3, 1))
    np.savez_compressed(
        rollout_path,
        thorax_positions=positions,
        thorax_quaternions=quaternions,
        timestep_s=np.asarray([0.1]),
    )
    digest = hashlib.sha256(rollout_path.read_bytes()).hexdigest()
    (dataset_root / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "dataset_id": "Healthy_001",
                "dataset_type": "healthy",
                "dataset_version": "1.0.0",
                "status": "VALIDATED",
                "source_commit": "0" * 40,
                "entries": [{"relative_path": "rollouts/rollout_arrays.npz", "sha256": digest}],
                "checksums": {"rollouts/rollout_arrays.npz": digest},
                "citation": "fixture",
                "scientific_scope": "computational fixture",
            }
        ),
        encoding="utf-8",
    )

    output = tmp_path / "results"
    result = ExecutionRuntime(ExecutionContext(tmp_path, output_root=output)).execute()

    assert result.state is ExecutionState.COMPLETED
    assert result.validation["completed"] == 1
    assert result.validation["validation_not_available"] == 1
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["completed"] == 1
    rollout_output = output / "rollouts" / "Healthy_001__rollout_arrays"
    for directory in ("analysis", "statistics", "validation", "reports", "figures", "publication"):
        assert (rollout_output / directory).is_dir(), directory
    assert (rollout_output / "figures" / "trajectory.png").is_file()
    assert (rollout_output / "figures" / "velocity.png").is_file()
    assert not (rollout_output / "figures" / "validation.png").exists()


def test_invalid_dataset_manifest_is_reported_without_pipeline_call(tmp_path: Path) -> None:
    dataset_root = tmp_path / "datasets" / "healthy" / "Healthy_bad"
    dataset_root.mkdir(parents=True)
    (dataset_root / "manifest.json").write_text(
        json.dumps(
            {
                "dataset_id": "Healthy_bad",
                "dataset_type": "healthy",
                "entries": [{"relative_path": "rollouts/data.txt"}],
            }
        ),
        encoding="utf-8",
    )
    result = ExecutionRuntime(ExecutionContext(tmp_path, output_root=tmp_path / "results")).execute()
    assert result.state is ExecutionState.INVALID_DATASET
    assert not (tmp_path / "results" / "summary.json").exists()
