"""Tests for orchestration-only Epic 20 campaign services."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

from drosophila_pd.research_campaign import (
    Campaign,
    CampaignManager,
    CampaignState,
    ExperimentSpec,
)


def _manager(tmp_path: Path) -> tuple[CampaignManager, Campaign, ExperimentSpec, ExperimentSpec]:
    manager = CampaignManager(tmp_path / "campaigns")
    campaign = manager.create(Campaign(name="integration", author="test"))
    first = manager.add_experiment(
        campaign.campaign_id,
        ExperimentSpec("exp_a", "first", config={"seed": 0}, priority=1, batch="a"),
    )
    second = manager.add_experiment(
        campaign.campaign_id,
        ExperimentSpec("exp_b", "second", config={"seed": 0}, dependencies=(first.experiment_id,), priority=2, batch="b"),
    )
    return manager, campaign, first, second


def test_dependency_scheduler_and_lifecycle(tmp_path: Path) -> None:
    manager, campaign, first, second = _manager(tmp_path)
    manager.queue(campaign.campaign_id)
    assert [item.experiment_id for item in manager.next_ready(campaign.campaign_id)] == [first.experiment_id]

    calls: list[str] = []

    def executor(experiment: ExperimentSpec) -> dict[str, object]:
        calls.append(experiment.experiment_id)
        return {"experiment_id": experiment.experiment_id, "validation": {"overall_pass": True}, "metrics": {"mae": 0.1}}

    manager.run(campaign.campaign_id, executor)
    assert calls == [first.experiment_id]
    assert manager.get(campaign.campaign_id).status == CampaignState.READY
    manager.run(campaign.campaign_id, executor)
    assert calls == [first.experiment_id, second.experiment_id]
    assert manager.get(campaign.campaign_id).status == CampaignState.COMPLETED
    assert {event.event_type for event in manager.history(campaign.campaign_id).events} >= {"created", "queued", "started", "experiment_completed"}


def test_pause_resume_cancel_and_retry(tmp_path: Path) -> None:
    manager, campaign, first, _ = _manager(tmp_path)
    manager.queue(campaign.campaign_id)
    manager.pause(campaign.campaign_id)
    assert manager.get(campaign.campaign_id).status == CampaignState.PAUSED
    manager.resume(campaign.campaign_id)
    assert manager.next_ready(campaign.campaign_id)[0].experiment_id == first.experiment_id
    manager.cancel(campaign.campaign_id)
    assert manager.get(campaign.campaign_id).status == CampaignState.CANCELLED

    retry_manager, retry_campaign, retry_first, _ = _manager(tmp_path / "retry")
    retry_manager.queue(retry_campaign.campaign_id)
    retry_manager.run(retry_campaign.campaign_id, lambda _: (_ for _ in ()).throw(RuntimeError("planned")))
    assert retry_first.state == CampaignState.FAILED
    retry_manager.retry(retry_campaign.campaign_id, retry_first.experiment_id)
    retry_manager.run(retry_campaign.campaign_id, lambda _: {"validation": {"overall_pass": True}})
    assert retry_first.state == CampaignState.COMPLETED


def test_persistence_manifest_validation_report_and_bundle(tmp_path: Path) -> None:
    manager, campaign, _, _ = _manager(tmp_path)
    manager.queue(campaign.campaign_id)
    manager.run(campaign.campaign_id, lambda experiment: {"validation": {"overall_pass": True}, "metrics": {"rmse": 0.2}})
    manager.run(campaign.campaign_id, lambda experiment: {"validation": {"overall_pass": True}, "metrics": {"rmse": 0.3}})

    validation = manager.validate(campaign.campaign_id)
    assert validation["overall_pass"] is True
    assert validation["experiment_count"] == 2
    report = manager.report(campaign.campaign_id, fmt="md")
    assert report.exists()
    manifest = manager.manifest(campaign.campaign_id).as_dict()
    assert manifest["git_commit"]
    assert manifest["configuration_hash"] == campaign.configuration_hash
    bundle = manager.bundle(campaign.campaign_id, tmp_path / "publication" / "campaign_bundle.zip")
    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())
    assert "manifest.json" in names
    assert "checksums/sha256.json" in names
    assert any(name.startswith("reports/") for name in names)
    assert all(name in names for name in ("validation/", "figures/", "tables/", "publication/"))

    state = tmp_path / "manager.json"
    manager.save(state)
    restored = CampaignManager.load(state)
    assert restored.get(campaign.campaign_id).configuration_hash == campaign.configuration_hash
    assert len(restored.history(campaign.campaign_id).events) == len(manager.history(campaign.campaign_id).events)


def test_validation_missing_result_and_dependency_error(tmp_path: Path) -> None:
    manager = CampaignManager(tmp_path / "campaigns")
    campaign = manager.create(Campaign(name="validation"))
    missing = manager.add_experiment(campaign.campaign_id, ExperimentSpec("missing", "missing", config={"seed": 1}))
    missing.result_path = (tmp_path / "does-not-exist.json").as_posix()
    result = manager.validate(campaign.campaign_id)
    assert result["overall_pass"] is False
    assert result["missing_results"] == ["missing"]
    manager.add_experiment(campaign.campaign_id, ExperimentSpec("bad", "bad", dependencies=("unknown",)))
    with pytest.raises(ValueError, match="unknown dependencies"):
        manager.queue(campaign.campaign_id)


def test_cli_help_and_create(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "research_campaign_cli.py"
    help_result = subprocess.run([sys.executable, str(script), "--help"], check=True, capture_output=True, text=True)
    assert "bundle" in help_result.stdout
    state = tmp_path / "cli.json"
    created = subprocess.run(
        [sys.executable, str(script), "create", "--name", "cli-campaign", "--state", str(state), "--root", str(tmp_path / "root")],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(created.stdout)
    assert payload["overall_pass"] is True
    assert state.exists()
