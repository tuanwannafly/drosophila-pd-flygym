from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.benchmarking import BenchmarkSuite  # noqa: E402
from drosophila_pd.debug_utils import DebugLogger, DiagnosticReport, StructuredEventLog, TimingTrace  # noqa: E402
from drosophila_pd.developer_tooling import ArchitectureSnapshot, DependencyGraphGenerator, ModuleIndex  # noqa: E402
from drosophila_pd.project_health import ProjectHealth  # noqa: E402
from drosophila_pd.release_engineering import ReleaseManifest, ReleaseNotesGenerator  # noqa: E402


def test_release_manifest_and_notes_are_serializable():
    manifest = ReleaseManifest(ROOT).build()
    assert manifest["version"] == "v1.0.0"
    assert manifest["metadata"]["source_commit"]
    assert manifest["compatibility"]
    markdown = ReleaseNotesGenerator().to_markdown(manifest)
    html = ReleaseNotesGenerator().to_html(manifest)
    assert "Release Engineering Report" in markdown
    assert "<html>" in html


def test_project_health_reports_expected_checks_without_importing_scientific_modules():
    report = ProjectHealth(ROOT).run()
    expected = {
        "missing_modules",
        "duplicate_modules",
        "unused_imports",
        "unused_exports",
        "dead_plugins",
        "circular_dependencies",
        "configuration_consistency",
        "documentation_coverage",
    }
    assert expected == set(report["checks"])
    assert report["overall_pass"] is True


def test_developer_tools_index_graph_hooks_and_architecture_snapshot():
    index = ModuleIndex(ROOT)
    modules = index.build()
    assert any(module["path"] == "web/plugin_platform.js" for module in modules)
    graph = DependencyGraphGenerator(index).build()
    assert "web/plugin_platform.js" in graph["nodes"]
    snapshot = ArchitectureSnapshot(ROOT).build()
    assert snapshot["hooks"]["hooks"]
    assert snapshot["hooks"]["capabilities"]
    assert snapshot["api"]["module_count"] == len(modules)


def test_debug_logger_timing_and_diagnostic_report():
    events = StructuredEventLog(clock=lambda: "fixed-time")
    logger = DebugLogger(events)
    logger.info("release.start", version="v1.0.0")
    ticks = iter((0.0, 0.25))
    with TimingTrace("operation", events, clock=lambda: next(ticks)):
        pass
    report = DiagnosticReport(events=events, health={"overall_pass": True}).build()
    assert report["event_log"]["event_count"] == 3
    assert report["event_log"]["events"][-1]["payload"]["elapsed_seconds"] == pytest.approx(0.25)
    assert report["scope"].startswith("Developer diagnostics")


def test_benchmark_suite_runs_only_registered_operations():
    suite = BenchmarkSuite(clock=iter((0.0, 0.1, 1.0, 1.1)).__next__)
    suite.register("Import", lambda: None)
    suite.register("Verification", lambda: None)
    report = suite.run(iterations=1)
    assert report["complete"] is True
    assert report["stage_count"] == 2
    assert report["stages"][0]["mean_seconds"] == pytest.approx(0.1)
    with pytest.raises(ValueError):
        suite.register("Simulation", lambda: None)
