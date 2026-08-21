"""Tests for orchestration and data management only.

These tests use caller-supplied metadata handlers and temporary files. They do
not execute FlyGym, MuJoCo, or create scientific rollout data.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.experiment import (  # noqa: E402
    ArtifactLayout,
    ARTIFACT_DIRECTORIES,
    DatasetManager,
    ExperimentBenchmark,
    ExperimentJob,
    ExperimentQueue,
    ExperimentRunner,
    ExperimentScheduler,
    ExperimentStatus,
    PublicationAssetManager,
    STAGE_NAMES,
    merge_dataset_managers,
)


def _handlers():
    return {stage: (lambda context, stage=stage: {"stage": stage, "job_id": context["job"].job_id}) for stage in STAGE_NAMES}


def test_runner_creates_layout_manifest_and_structured_log(tmp_path):
    job = ExperimentJob("job_a", {"seed": 0}, tmp_path)
    result = ExperimentRunner(_handlers()).run(job)

    assert result.status is ExperimentStatus.COMPLETED
    assert result.error is None
    root = tmp_path / "job_a"
    assert set(result.artifact_paths) == set(ARTIFACT_DIRECTORIES)
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "COMPLETED"
    assert manifest["configuration_hash"]
    assert (root / "logs" / "experiment.jsonl").read_text(encoding="utf-8").count("\n") >= len(STAGE_NAMES) + 2


def test_scheduler_retries_failed_job_and_skips_completed(tmp_path):
    calls = {stage: 0 for stage in STAGE_NAMES}

    def flaky(context):
        calls["rollout"] += 1
        if calls["rollout"] == 1:
            raise RuntimeError("transient")
        return {"ok": True}

    handlers = _handlers()
    handlers["rollout"] = flaky
    job = ExperimentJob("job_retry", {}, tmp_path, max_retries=1)
    progress = []
    results = ExperimentScheduler(ExperimentRunner(handlers)).run(
        ExperimentQueue([job]), progress_callback=progress.append
    )

    assert [result.status for result in results] == [ExperimentStatus.FAILED, ExperimentStatus.COMPLETED]
    assert job.attempts == 2
    assert progress[-1]["status"] == "COMPLETED"
    assert not ExperimentScheduler(ExperimentRunner(handlers)).resume([job])


def test_missing_handlers_fail_explicitly_without_simulation(tmp_path):
    result = ExperimentRunner({}).run(ExperimentJob("missing", {}, tmp_path))
    assert result.status is ExperimentStatus.FAILED
    assert "explicit handlers" in result.error
    assert json.loads(result.manifest_path.read_text(encoding="utf-8"))["status"] == "FAILED"


def test_dataset_layout_register_verify_split_and_merge(tmp_path):
    source_a = tmp_path / "a.json"
    source_b = tmp_path / "b.json"
    source_a.write_text('{"condition":"Healthy"}', encoding="utf-8")
    source_b.write_text('{"condition":"Candidate"}', encoding="utf-8")
    manager = DatasetManager(tmp_path / "dataset", dataset_id="real_inputs")
    manager.initialize()
    manager.register_file(source_a, "healthy", record_id="a", copy=True)
    manager.register_file(source_b, "candidate", record_id="b", copy=True)

    assert (tmp_path / "dataset" / "manifest.json").is_file()
    assert (tmp_path / "dataset" / "checksum.json").is_file()
    assert manager.verify()["overall_pass"] is True
    assert sum(len(part) for part in manager.split(fractions={"train": 0.5, "test": 0.5}).values()) == 2
    loaded = DatasetManager.load(tmp_path / "dataset")
    assert loaded.verify()["overall_pass"] is True

    merged = merge_dataset_managers([manager], tmp_path / "merged", dataset_id="merged")
    assert merged.verify()["overall_pass"] is True
    with pytest.raises(ValueError, match="duplicate"):
        merged.register_file(source_a, "healthy", record_id="a", copy=True)


def test_publication_assets_copy_only_existing_files(tmp_path):
    layout = ArtifactLayout(tmp_path / "experiment")
    layout.prepare()
    figure = tmp_path / "figure.png"
    table = tmp_path / "table.csv"
    figure.write_bytes(b"PNG metadata placeholder from caller")
    table.write_text("metric,value\n", encoding="utf-8")
    manager = PublicationAssetManager(layout)
    manager.register_figure(figure, caption="Caller-provided figure")
    manager.register_table(table, caption="Caller-provided table")
    files = manager.write_manifests()
    assert all(path.is_file() for path in files.values())
    assert json.loads(files["figures"].read_text(encoding="utf-8"))["figures"][0]["identifier"] == "Figure 1"


def test_benchmark_measures_only_registered_operations():
    benchmark = ExperimentBenchmark()
    benchmark.register("Import", lambda: {"source": "caller"})
    benchmark.register("Analysis", lambda: 1)
    report = benchmark.run(repeats=1, cache_metrics={"hits": 1, "misses": 0})
    assert report["registered_operations"] == ["Analysis", "Import"]
    assert report["memory_and_cpu_measured"] is True
    assert report["operations"]["Import"]["output_hash"]
