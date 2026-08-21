"""Tests for Project Y campaign planning and tracking."""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from drosophila_pd.campaign import (
    Campaign,
    CampaignLogger,
    CampaignManager,
    CampaignScheduler,
    CampaignStatus,
)


ROOT = Path(__file__).parents[1]
TEMPLATES = ROOT / "configs" / "campaign_templates"


def test_all_campaign_templates_are_planning_only() -> None:
    expected = {"healthy", "pd", "candidate", "control", "validation", "benchmark", "longitudinal", "perturbation", "recovery", "drug_screening"}
    assert {path.stem for path in TEMPLATES.glob("*.yaml")} == expected
    for path in TEMPLATES.glob("*.yaml"):
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert payload["status"] == "PLANNED"
        assert payload["execution_enabled"] is False
        assert payload["guardrails"]["no_simulation_during_planning"] is True
        assert payload["guardrails"]["no_fabricated_data"] is True


def test_template_manager_matrix_state_machine_and_queue(tmp_path: Path) -> None:
    manager = CampaignManager(tmp_path / "campaigns")
    campaign = manager.create_from_template(TEMPLATES / "healthy.yaml")
    assert campaign.status == CampaignStatus.PLANNED
    assert len(campaign.matrix) == 1
    assert campaign.matrix[0]["dataset"] == "PENDING_DATASET"

    scheduler = CampaignScheduler(manager)
    assert scheduler.prepare(campaign.campaign_id, dataset_available=False) == CampaignStatus.WAITING_DATASET
    assert manager.progress(campaign.campaign_id).waiting == 1
    assert scheduler.prepare(campaign.campaign_id, dataset_available=True) == CampaignStatus.READY
    assert scheduler.enqueue(campaign.campaign_id) == campaign.campaign_id
    assert scheduler.dispatch() == (campaign.campaign_id,)
    assert campaign.status == CampaignStatus.QUEUED

    manager.transition(campaign.campaign_id, CampaignStatus.RUNNING)
    experiment_id = campaign.matrix[0]["experiment_id"]
    manager.record_experiment(campaign.campaign_id, experiment_id, CampaignStatus.COMPLETED)
    manager.transition(campaign.campaign_id, CampaignStatus.COMPLETED)
    assert manager.progress(campaign.campaign_id).completed == 1


def test_matrix_expansion_preserves_execution_dimensions(tmp_path: Path) -> None:
    manager = CampaignManager(tmp_path)
    campaign = Campaign(
        name="matrix",
        metadata={"matrix": {
            "dataset": ["healthy", "candidate"],
            "seed": [0, 1],
            "controller": ["controller_a"],
            "terrain": ["flat"],
            "noise": [False, True],
            "perturbation": ["none"],
            "duration": [0.5],
            "replicates": 2,
            "priority": 3,
        }},
        expected_outputs=["analysis", "validation"],
    )
    manager.create(campaign)
    assert len(campaign.matrix) == 16
    assert {row["dataset"] for row in campaign.matrix} == {"healthy", "candidate"}
    assert {row["seed"] for row in campaign.matrix} == {0, 1}
    assert {row["replicate"] for row in campaign.matrix} == {1, 2}
    assert all(row["expected_outputs"] == ["analysis", "validation"] for row in campaign.matrix)


def test_scheduler_orders_campaigns_by_priority(tmp_path: Path) -> None:
    manager = CampaignManager(tmp_path)
    low = manager.create(Campaign(name="low", priority=1), expand=False)
    high = manager.create(Campaign(name="high", priority=5), expand=False)
    scheduler = CampaignScheduler(manager)
    for campaign in (low, high):
        scheduler.prepare(campaign.campaign_id, dataset_available=True)
        scheduler.enqueue(campaign.campaign_id)
    assert scheduler.dispatch() == (high.campaign_id, low.campaign_id)


def test_dashboard_publication_plan_persistence_and_logger(tmp_path: Path) -> None:
    manager = CampaignManager(tmp_path / "campaigns")
    campaign = manager.create_from_template(TEMPLATES / "validation.yaml")
    dashboard = manager.write_dashboard(campaign.campaign_id, tmp_path / "dashboard")
    publication = manager.write_publication_plan(campaign.campaign_id, tmp_path / "publication")
    assert {path.name for path in dashboard.values()} == {
        "campaign_summary.json",
        "campaign_status.csv",
        "campaign_progress.md",
        "campaign_health.json",
        "campaign_inventory.csv",
    }
    assert {path.name for path in publication.values()} == {
        "figure_plan.md",
        "table_plan.md",
        "experiment_mapping.csv",
        "supplement_mapping.csv",
        "reviewer_checklist.md",
        "publication_readiness.md",
    }
    for path in (*dashboard.values(), *publication.values()):
        assert path.is_file()
    manifest = manager.manifest(campaign.campaign_id).as_dict()
    assert manifest["configuration_hash"] == campaign.configuration_hash
    state_path = manager.save(tmp_path / "state.json")
    restored = CampaignManager.load(state_path, root=tmp_path / "restored")
    assert restored.get(campaign.campaign_id).name == campaign.name

    log_path = tmp_path / "campaign.log"
    CampaignLogger(log_path).log("planned", campaign_id=campaign.campaign_id, status=campaign.status.value)
    assert json.loads(log_path.read_text(encoding="utf-8"))["event"] == "planned"


def test_invalid_state_transition_is_rejected(tmp_path: Path) -> None:
    manager = CampaignManager(tmp_path)
    campaign = manager.create(Campaign(name="state"), expand=False)
    try:
        manager.transition(campaign.campaign_id, CampaignStatus.COMPLETED)
    except ValueError as error:
        assert "invalid campaign transition" in str(error)
    else:
        raise AssertionError("invalid transition was accepted")
