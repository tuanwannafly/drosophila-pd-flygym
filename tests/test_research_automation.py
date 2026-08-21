"""Tests for metadata-only Milestone 3 automation services."""

from __future__ import annotations

import json
from pathlib import Path
import sys

from drosophila_pd.automation import (
    ArtifactManager,
    BenchmarkCenter,
    DatasetCatalog,
    DeveloperToolkit,
    ExperimentQueueManager,
    ProjectHealthMonitor,
    PublicationBuilder,
    ReproducibilityCenter,
    ResearchAutomationPlatform,
)
from drosophila_pd.experiment import ExperimentJob, STAGE_NAMES
from drosophila_pd.research_execution import (
    ExecutionContext,
    ExecutionJob,
    ExecutionQueue,
    ResearchAutomation,
    load_campaign_plan,
)

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from research_automation_cli import main  # noqa: E402


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _handlers():
    return {stage: (lambda context, stage=stage: {"stage": stage, "job_id": context["job"].job_id}) for stage in STAGE_NAMES}


def test_dataset_catalog_versions_search_and_integrity(tmp_path):
    source = tmp_path / "rollout.json"
    source.write_text('{"source":"caller"}', encoding="utf-8")
    catalog = DatasetCatalog(tmp_path / "catalog")
    entry = catalog.add(source, dataset_id="healthy-001", name="healthy", version_name="v1", tags=("adult",), species="Drosophila")

    assert catalog.get(entry.dataset_id).sha256
    assert [item.dataset_id for item in catalog.search("adult")] == ["healthy-001"]
    assert len(catalog.versions("healthy")) == 1
    assert catalog.verify()["overall_pass"] is True
    loaded = DatasetCatalog.load(tmp_path / "catalog" / "dataset_catalog.json")
    assert loaded.verify()["overall_pass"] is True
    source.write_text('{"source":"changed"}', encoding="utf-8")
    assert loaded.verify()["overall_pass"] is False


def test_experiment_queue_manager_persists_progress_and_cancel(tmp_path):
    manager = ExperimentQueueManager(tmp_path / "queue")
    job = ExperimentJob("job-a", {"seed": 0}, tmp_path / "runs")
    manager.enqueue(job)
    results = manager.run(stage_handlers=_handlers())

    assert results[0].status.value == "COMPLETED"
    assert manager.status()["counts"]["COMPLETED"] == 1
    assert manager.state_path.is_file()
    loaded = ExperimentQueueManager.load(manager.state_path)
    assert loaded.status()["counts"]["COMPLETED"] == 1

    cancelled = loaded.enqueue(ExperimentJob("job-b", {}, tmp_path / "runs"))
    loaded.cancel(cancelled.job_id)
    assert cancelled.status.value == "CANCELLED"


def test_reproducibility_artifact_publication_and_benchmark_services(tmp_path):
    source = tmp_path / "input.json"
    source.write_text("{}", encoding="utf-8")
    repro = ReproducibilityCenter(Path(__file__).parents[1])
    manifest = repro.collect(campaign_id="test", configuration={"seed": 0}, dataset_paths=[source], seeds=[0])
    assert manifest["configuration_hash"]
    assert repro.verify(manifest)["overall_pass"] is True

    artifacts = ArtifactManager(tmp_path / "artifacts")
    artifacts.prepare()
    artifacts.register_file(source, "json")
    artifact_manifest = artifacts.write_manifest()
    assert artifact_manifest.is_file()
    assert artifacts.verify()["overall_pass"] is True

    publication = PublicationBuilder(tmp_path / "publication")
    target = publication.register(source, "metadata")
    assert target.is_file()
    assert publication.build().is_file()

    benchmark = BenchmarkCenter()
    benchmark.register("Import", lambda: source.read_text(encoding="utf-8"))
    assert benchmark.run()["complete"] is True
    assert benchmark.not_run_report()["status"] == "not_run"


def test_health_toolkit_platform_and_cli_are_non_simulation(tmp_path):
    root = Path(__file__).parents[1]
    health = ProjectHealthMonitor(root).run()
    assert health["overall_pass"] is True
    toolkit = DeveloperToolkit(root)
    assert toolkit.api_report()["module_count"] > 0
    assert toolkit.dependency_report()["nodes"]
    assert toolkit.test_report()["test_count"] > 0

    platform = ResearchAutomationPlatform(root, tmp_path / "outputs")
    output = platform.write_manifest()
    assert json.loads(output.read_text(encoding="utf-8"))["scientific_scope"]
    assert main(["--root", str(root), "health-check"]) == 0


def test_campaign_plan_reads_all_existing_healthy_rows():
    plan = load_campaign_plan(ExecutionContext(REPOSITORY_ROOT))
    assert plan.experiment_count == 100
    assert plan.rows[0]["experiment_id"] == "Healthy_001"
    assert plan.rows[-1]["experiment_id"] == "Healthy_100"
    assert plan.rows[0]["seed"] == 0
    assert plan.rows[-1]["seed"] == 99


def test_campaign_pattern_is_expanded_without_hardcoded_condition(tmp_path):
    campaign_root = tmp_path / "campaigns" / "candidate"
    campaign_root.mkdir(parents=True)
    (campaign_root / "campaign.yaml").write_text(
        """
campaign_id: candidate_campaign
experiment_id_pattern: Candidate_[007-009]
seed_policy:
  values: 10-12
""",
        encoding="utf-8",
    )
    plan = load_campaign_plan(ExecutionContext(tmp_path, campaign_id="candidate", campaign_root=tmp_path / "campaigns"))
    assert [row["experiment_id"] for row in plan.rows] == ["Candidate_007", "Candidate_008", "Candidate_009"]
    assert [row["seed"] for row in plan.rows] == [10, 11, 12]


def test_missing_campaign_does_not_fallback_to_healthy(tmp_path):
    plan = load_campaign_plan(ExecutionContext(tmp_path, campaign_id="candidate", campaign_root=tmp_path / "campaigns"))
    assert plan.rows == ()


def test_execution_queue_round_trips_required_job_fields(tmp_path):
    queue = ExecutionQueue(tmp_path / "progress")
    queue.enqueue(ExecutionJob(id="Healthy_001", dataset="Healthy_001", seed=0, status="READY", retry_count=2))
    queue.save()
    restored = ExecutionQueue.load(tmp_path / "progress" / "jobs.json")
    job = restored.get("Healthy_001")
    assert job.dataset == "Healthy_001"
    assert job.seed == 0
    assert job.status == "READY"
    assert job.retry_count == 2
    assert restored.counts()["READY"] == 1


def test_automation_waits_for_real_datasets_and_writes_progress(tmp_path):
    context = ExecutionContext(
        REPOSITORY_ROOT,
        dataset_root=tmp_path / "datasets",
        output_root=tmp_path / "execution",
    )
    progress_root = tmp_path / "progress"
    automation = ResearchAutomation(context, progress_root=progress_root)
    payload = automation.execute()
    assert payload["total"] == 100
    assert payload["completed"] == 0
    assert payload["waiting"] == 100
    assert payload["failed"] == 0
    assert (progress_root / "progress.json").is_file()
    assert (progress_root / "progress.csv").is_file()
    assert (progress_root / "progress.md").is_file()
    assert (progress_root / "research_summary.md").is_file()
    persisted = json.loads((progress_root / "jobs.json").read_text(encoding="utf-8"))
    assert len(persisted["jobs"]) == 100


def test_resume_does_not_reset_completed_jobs(tmp_path):
    context = ExecutionContext(REPOSITORY_ROOT, dataset_root=tmp_path / "datasets", output_root=tmp_path / "execution")
    automation = ResearchAutomation(context, progress_root=tmp_path / "progress")
    automation.plan()
    job = automation.queue.get("Healthy_001")
    job.status = "COMPLETED"
    job.duration = 1.0
    automation.queue.save()
    payload = automation.execute()
    assert payload["completed"] == 1
    assert payload["waiting"] == 99
