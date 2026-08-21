"""Epic 18 release-candidate and unified-dashboard contracts."""

from __future__ import annotations

import json
from pathlib import Path

from drosophila_pd.release_candidate import ReleaseCandidateBuilder, ReleaseCandidateConfig


ROOT = Path(__file__).parents[1]


def test_release_candidate_builder_is_static_and_scoped(tmp_path):
    builder = ReleaseCandidateBuilder(ROOT, ReleaseCandidateConfig(version="test-rc"))

    report = builder.write(tmp_path)

    assert report["release_candidate"] is True
    assert report["validation_summary"]["simulation_executed"] is False
    assert report["validation_summary"]["evidence_modified"] is False
    assert report["performance_report"]["simulation_executed"] is False
    for name in (
        "release.json",
        "release.md",
        "release.html",
        "module_index.json",
        "api_index.json",
        "dependency_graph.json",
        "dependency_graph.dot",
        "plugin_registry.json",
        "health_report.json",
        "validation_summary.json",
        "coverage_report.json",
        "performance_report.json",
        "artifact_manifest.json",
        "architecture.pdf.note",
    ):
        assert (tmp_path / name).is_file(), name
    assert json.loads((tmp_path / "release.json").read_text(encoding="utf-8"))["version"] == "test-rc"


def test_unified_dashboard_keeps_existing_services_and_scope():
    text = (ROOT / "web" / "laboratory_dashboard.js").read_text(encoding="utf-8")
    app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    required = [
        "LaboratoryDashboard",
        "Digital Parkinson Laboratory",
        "Datasets",
        "Experiments",
        "Digital Fly",
        "Analysis",
        "Reports",
        "Publication",
        "Plugins",
        "no biological interpretation",
    ]
    assert all(marker.lower() in text.lower() for marker in required)
    assert "this.laboratoryDashboard" in app
    assert "this.laboratoryDashboard.render" in app


def test_release_candidate_does_not_change_frozen_paths():
    import subprocess

    result = subprocess.run(["git", "diff", "--name-only", "HEAD~1"], cwd=ROOT, capture_output=True, text=True, check=False)
    changed = set(result.stdout.splitlines()) if result.returncode == 0 else set()
    assert not any(
        path.startswith(("results/", "docs/report/", "dist/"))
        or (path.startswith("notebooks/") and not path.startswith("notebooks/colab/"))
        for path in changed
    )
