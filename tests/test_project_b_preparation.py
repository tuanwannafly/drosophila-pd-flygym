"""Planning-contract checks for Project B.

These tests validate planning assets and the existing dataset gate only. They
never execute FlyGym, MuJoCo, or a scientific rollout.
"""

from __future__ import annotations

import csv
import copy
import json
import re
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).parents[1]
CAMPAIGN = ROOT / "research" / "campaigns" / "parkinson_study"
DOCS = ROOT / "docs" / "v10" / "Project_B"
PAPER = ROOT / "paper" / "parkinson_study"


def test_project_b_matrix_has_exactly_100_planned_experiments() -> None:
    rows = list(csv.DictReader((CAMPAIGN / "experiment_matrix.csv").open(newline="", encoding="utf-8-sig")))

    assert len(rows) == 100
    assert [row["experiment_id"] for row in rows] == [f"PD_{i:03d}" for i in range(1, 101)]
    assert [int(row["seed"]) for row in rows] == list(range(100))
    assert {row["status"] for row in rows} == {"PLANNED"}
    required = {
        "experiment_id",
        "seed",
        "configuration",
        "expected_outputs",
        "validation_profile",
        "publication_targets",
    }
    assert required <= set(rows[0])
    assert all(row["configuration"].startswith("PENDING_") for row in rows)
    assert all(row["expected_outputs"] for row in rows)


def test_project_b_campaign_and_templates_are_guarded() -> None:
    campaign = yaml.safe_load((CAMPAIGN / "campaign.yaml").read_text(encoding="utf-8"))
    schema = json.loads((CAMPAIGN / "manifest.schema.json").read_text(encoding="utf-8"))
    template = json.loads((CAMPAIGN / "dataset_manifest.template.json").read_text(encoding="utf-8"))
    metadata = yaml.safe_load((CAMPAIGN / "metadata.template.yaml").read_text(encoding="utf-8"))
    checksum = json.loads((CAMPAIGN / "checksum.template.json").read_text(encoding="utf-8"))

    assert campaign["status"] == "PLANNING_ONLY"
    assert campaign["execution_enabled"] is False
    assert campaign["experiment_count"] == 100
    assert schema["properties"]["dataset_type"]["const"] == "pd"
    assert template["status"] == "PLANNING_ONLY"
    assert template["dataset_type"] == "pd"
    assert template["entries"] == []
    assert template["checksums"] == {}
    assert metadata["status"] == "PLANNED"
    assert checksum["status"] == "PLANNING_ONLY"


def test_project_b_manifest_schema_accepts_only_execution_ready_provenance() -> None:
    schema = json.loads((CAMPAIGN / "manifest.schema.json").read_text(encoding="utf-8"))
    template = json.loads((CAMPAIGN / "dataset_manifest.template.json").read_text(encoding="utf-8"))
    candidate = copy.deepcopy(template)
    candidate["source_commit"] = "0" * 40

    jsonschema.validate(candidate, schema)


def test_project_b_docs_and_paper_skeleton_exist() -> None:
    assert {
        "README.md",
        "dataset_requirements.md",
        "expected_directory_tree.md",
        "execution_flow.md",
        "cli_waiting_dataset.md",
        "manual_checklist.md",
    } <= {path.name for path in DOCS.glob("*.md")}
    assert {path.name for path in PAPER.glob("*.md")} == {
        "Introduction.md",
        "Methods.md",
        "Results.md",
        "Discussion.md",
        "Supplementary.md",
    }


def test_project_b_local_markdown_links_resolve() -> None:
    link_pattern = re.compile(r"\]\(([^)#]+)(?:#[^)]+)?\)")
    for root in (CAMPAIGN, DOCS, PAPER):
        for document in root.glob("*.md"):
            for target in link_pattern.findall(document.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (document.parent / target).resolve()
                assert resolved.is_file() or resolved.is_dir(), (document, target)


def test_existing_dataset_cli_reports_waiting_dataset(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/dataset_cli.py", "status", "--output", str(tmp_path / "status")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    report = json.loads(result.stdout)
    assert report["state"] == "WAITING_DATASET"
    assert report["datasets_found"] == 0


def test_project_b_contains_no_rollout_payloads() -> None:
    assert not list(CAMPAIGN.rglob("*.npy"))
    assert not list(CAMPAIGN.rglob("*.npz"))
    assert not list(CAMPAIGN.rglob("*.mp4"))
    assert [path.name for path in CAMPAIGN.rglob("*.csv")] == ["experiment_matrix.csv"]
