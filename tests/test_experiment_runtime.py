"""V8 experiment runtime lifecycle tests.

Fixtures are structural intake files only. The downstream callable is injected
for the READY contract test so no simulation or scientific result is produced.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from drosophila_pd.experiment_runtime import (
    EventLog,
    ExperimentContext,
    ExperimentEventType,
    ExperimentRuntime,
    ExperimentSession,
    SessionState,
)


def test_waiting_dataset_persists_complete_runtime_state(tmp_path: Path) -> None:
    output = tmp_path / "experiment"
    runtime = ExperimentRuntime(ExperimentContext(tmp_path, output_root=output))
    summary = runtime.run()

    assert summary["state"] == SessionState.WAITING_DATASET
    assert summary["dataset"]["missing_types"]
    for name in ("session.json", "execution.json", "runtime_state.json", "artifacts.json", "manifest.json", "experiment_summary.json", "experiment_summary.md"):
        assert (output / name).is_file(), name
    events = EventLog.load(output / "execution.json")
    assert [item.event for item in events.events] == [ExperimentEventType.SESSION_CREATED, ExperimentEventType.WAITING_DATASET]
    assert ExperimentSession.load(output / "session.json").state == SessionState.WAITING_DATASET


def test_ready_dataset_binds_and_calls_one_downstream_runner(tmp_path: Path) -> None:
    dataset_root = tmp_path / "datasets" / "healthy" / "1.0.0"
    rollout = dataset_root / "rollouts" / "trajectory.csv"
    rollout.parent.mkdir(parents=True)
    rollout.write_text("frame,x,y,z\n0,0,0,0\n1,1,0,0\n", encoding="utf-8")
    digest = hashlib.sha256(rollout.read_bytes()).hexdigest()
    (dataset_root / "metadata.json").write_text(json.dumps({"fixture": True}), encoding="utf-8")
    (dataset_root / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "dataset_id": "ready_fixture",
                "dataset_type": "healthy",
                "dataset_version": "1.0.0",
                "status": "VALIDATED",
                "source_commit": "0" * 40,
                "entries": [{"relative_path": "rollouts/trajectory.csv", "sha256": digest, "byte_size": rollout.stat().st_size}],
                "checksums": {"rollouts/trajectory.csv": digest},
                "citation": "fixture",
                "scientific_scope": "fixture only",
            }
        ),
        encoding="utf-8",
    )
    calls: list[str] = []
    output = tmp_path / "experiment"

    def downstream(request, _repository_root: Path, output_root: Path):
        calls.append(request.datasets[0].dataset_id)
        study_root = output_root / request.study_id
        report = study_root / "reports" / "study_report.json"
        report.parent.mkdir(parents=True)
        report.write_text("{}\n", encoding="utf-8")
        package = study_root / "research_package.zip"
        package.write_bytes(b"fixture package")
        return SimpleNamespace(
            study_root=study_root,
            package_path=package,
            validation={"overall_pass": True},
        )

    runtime = ExperimentRuntime(ExperimentContext(tmp_path, output_root=output), study_runner=downstream)
    summary = runtime.run()

    assert calls == ["ready_fixture"]
    assert summary["state"] == SessionState.COMPLETED
    assert summary["validation"]["overall_pass"] is True
    event_names = [item["event"] for item in json.loads((output / "execution.json").read_text(encoding="utf-8"))["events"]]
    assert event_names == [
        "SESSION_CREATED",
        "DATASET_READY",
        "PIPELINE_STARTED",
        "PIPELINE_COMPLETED",
        "VALIDATION_COMPLETED",
        "PACKAGE_CREATED",
    ]
    assert (output / "artifacts.json").is_file()


def test_runtime_cli_commands_wait_without_dataset(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "experiment_runtime.py"
    for command in ("prepare", "bind", "run", "status", "summary", "archive"):
        result = subprocess.run(
            [sys.executable, str(script), command, "--root", str(tmp_path), "--output", str(tmp_path / "output")],
            check=True,
            capture_output=True,
            text=True,
        )
        assert json.loads(result.stdout)["state"] == SessionState.WAITING_DATASET

    summary = json.loads((tmp_path / "output" / "experiment_summary.json").read_text(encoding="utf-8"))
    assert [item["status"] for item in summary["stages"]] == [SessionState.WAITING_DATASET] * 5
