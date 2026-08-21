"""Contract checks for the V5 Healthy campaign planning assets."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
CAMPAIGN = ROOT / "research" / "campaigns" / "healthy_baseline"
PUBLICATION = ROOT / "research" / "publication" / "healthy_baseline"


def test_healthy_campaign_matrix_is_deterministic_and_planning_only() -> None:
    rows = list(csv.DictReader((CAMPAIGN / "experiment_matrix.csv").open(newline="", encoding="utf-8")))

    assert len(rows) == 100
    assert [row["experiment_id"] for row in rows] == [f"Healthy_{index:03d}" for index in range(1, 101)]
    assert [int(row["seed"]) for row in rows] == list(range(100))
    assert {row["status"] for row in rows} == {"PLANNED"}
    assert {row["configuration"] for row in rows} == {"configs/experiments/healthy_baseline.yaml"}


def test_campaign_and_manifest_templates_preserve_execution_guard() -> None:
    campaign = yaml.safe_load((CAMPAIGN / "campaign.yaml").read_text(encoding="utf-8"))
    manifest = json.loads((CAMPAIGN / "dataset_manifest.template.json").read_text(encoding="utf-8"))
    checksum = json.loads((CAMPAIGN / "checksum.template.json").read_text(encoding="utf-8"))

    assert campaign["status"] == "PLANNING_ONLY"
    assert campaign["execution_enabled"] is False
    assert campaign["experiment_count"] == 100
    assert manifest["status"] == "PLANNING_ONLY"
    assert manifest["entries"] == []
    assert manifest["checksums"] == {}
    assert checksum["status"] == "PLANNING_ONLY"
    assert checksum["files"] == {}


def test_planning_notebook_has_no_code_or_outputs() -> None:
    notebook = json.loads((CAMPAIGN / "research_notebook_template.ipynb").read_text(encoding="utf-8"))

    assert notebook["nbformat"] == 4
    assert notebook["cells"]
    assert all(cell["cell_type"] == "markdown" for cell in notebook["cells"])
    assert all("outputs" not in cell for cell in notebook["cells"])
    assert all("execution_count" not in cell for cell in notebook["cells"])


def test_publication_layout_is_present_without_rollout_payloads() -> None:
    expected = {"figures", "tables", "methods", "results", "discussion", "supplementary", "references", "assets"}
    assert {path.name for path in PUBLICATION.iterdir() if path.is_dir()} == expected
    assert not list(CAMPAIGN.rglob("rollout"))
    assert not list(CAMPAIGN.rglob("*.npy"))
    assert not list(CAMPAIGN.rglob("*.npz"))
    assert not list(CAMPAIGN.rglob("*.mp4"))
