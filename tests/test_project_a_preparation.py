"""Planning-contract checks for Project A Healthy baseline assets.

These tests validate schemas, paths, and planning metadata only. They do not
execute FlyGym, parse rollout arrays, or create scientific outputs.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import yaml


ROOT = Path(__file__).parents[1]
CAMPAIGN = ROOT / "research" / "campaigns" / "healthy_baseline"
DOCS = ROOT / "docs" / "v10"
PAPER = ROOT / "paper" / "healthy_baseline"


def test_project_a_matrix_and_configuration_are_complete() -> None:
    rows = list(csv.DictReader((CAMPAIGN / "experiment_matrix.csv").open(newline="", encoding="utf-8")))

    assert len(rows) == 100
    assert [row["experiment_id"] for row in rows] == [f"Healthy_{i:03d}" for i in range(1, 101)]
    assert [int(row["seed"]) for row in rows] == list(range(100))
    assert {row["status"] for row in rows} == {"PLANNED"}
    required_columns = {
        "experiment_id",
        "seed",
        "configuration",
        "expected_outputs",
        "validation_profile",
        "publication_targets",
    }
    assert required_columns <= set(rows[0])
    assert (ROOT / rows[0]["configuration"]).is_file()


def test_project_a_templates_are_schema_and_manifest_safe() -> None:
    schema = json.loads((CAMPAIGN / "manifest.schema.json").read_text(encoding="utf-8"))
    template = json.loads((CAMPAIGN / "dataset_manifest.template.json").read_text(encoding="utf-8"))
    metadata = yaml.safe_load((CAMPAIGN / "metadata.template.yaml").read_text(encoding="utf-8"))

    assert schema["type"] == "object"
    assert set(schema["required"]) >= {"dataset_id", "dataset_type", "dataset_version", "entries", "checksums"}
    assert template["status"] == "PLANNING_ONLY"
    assert template["dataset_type"] == "healthy"
    assert template["entries"] == []
    assert template["checksums"] == {}
    assert metadata["status"] == "PLANNED"


def test_project_a_required_docs_and_assets_exist() -> None:
    expected_docs = {
        "133_Healthy_Dataset_Contract.md",
        "134_Experiment_Specification.md",
        "135_Metrics_Catalog.md",
        "136_Figure_Specification.md",
        "137_Table_Specification.md",
        "138_Publication_Skeleton.md",
        "139_Reviewer_Package.md",
        "140_ProjectA_Architecture.md",
    }
    assert expected_docs <= {path.name for path in DOCS.glob("*.md")}

    assert {path.name for path in PAPER.glob("*.md")} == {
        "methods.md",
        "results.md",
        "discussion.md",
        "limitations.md",
        "supplementary.md",
        "references.md",
    }
    assert {
        "healthy_dataset_contract.md",
        "metrics_catalog.md",
        "review_checklist.md",
        "reproducibility_checklist.md",
        "artifact_inventory.md",
        "validation_inventory.md",
    } <= {path.name for path in CAMPAIGN.glob("*.md")}


def test_project_a_docs_link_to_existing_local_targets() -> None:
    markdown_link = re.compile(r"\]\(([^)#]+)(?:#[^)]+)?\)")
    roots = [DOCS, CAMPAIGN, PAPER]

    for root in roots:
        for document in root.glob("*.md"):
            for target in markdown_link.findall(document.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (document.parent / target).resolve()
                assert resolved.is_file() or resolved.is_dir(), (document, target)


def test_project_a_assets_are_explicitly_planning_only() -> None:
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [CAMPAIGN / "healthy_dataset_contract.md", DOCS / "140_ProjectA_Architecture.md"]
    ).lower()

    assert "planning-only" in text
    assert "no rollout" in text
    assert "biological validation" in text
