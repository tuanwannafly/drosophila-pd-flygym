"""Milestone 4 tests for imported-state Digital Twin management."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from drosophila_pd.behavior_platform.digital_twin import DigitalTwin, TwinConfiguration, TwinMetadata, TwinState
from drosophila_pd.digital_twin_platform import (
    CollaborationLayer,
    DigitalTwinManager,
    DigitalTwinPlatform,
    KnowledgeGraph,
    ScenarioWorkspace,
    StateDiffEngine,
    TemporalExplorer,
    TwinAnnotation,
    VirtualLaboratorySession,
)

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from digital_twin_platform_cli import main as digital_twin_cli  # noqa: E402


def _twin(twin_id: str = "fly-1") -> DigitalTwin:
    configuration = TwinConfiguration("cfg", "1", {"source": "imported-rollout"})
    twin = DigitalTwin(TwinMetadata(twin_id, tags=("imported",)), configuration)
    for time_s, label, speed in ((0.0, "Idle", 0.0), (1.0, "Walk", 1.0), (2.0, "Turn", 0.5)):
        twin = twin.record_state(
            TwinState(
                time_s=time_s,
                state_label=label,
                metrics={"joint_angle": speed, "com_x": speed, "trajectory_x": speed, "existing_speed": speed},
                parameters={"controller": "imported"},
                metadata={"event": label.lower()},
            )
        )
    return twin


def test_twin_manager_snapshot_restore_branch_bookmark_annotation_and_json(tmp_path):
    manager = DigitalTwinManager()
    record = manager.register_imported_rollout(_twin(), "rollout-1", role="Candidate")
    manager.snapshot(record.twin_id, "early", time_s=1.0, bookmark="onset")
    manager.snapshot(record.twin_id, "latest")
    restored = manager.restore(record.twin_id, "early")
    assert restored.state_label == "Walk"
    branch = manager.branch(record.twin_id, "early", "fly-branch")
    assert branch.state.time_s == 1.0
    diff = manager.compare_snapshots(record.twin_id, "early", "latest")
    assert diff.metrics_delta["existing_speed"]["delta"] == pytest.approx(-0.5)
    assert diff.behavior_delta == {"left": "Walk", "right": "Turn"}
    manager.annotate(TwinAnnotation("a1", record.twin_id, "comment", "inspect turn", author="reviewer"))

    path = manager.to_json(tmp_path / "twins.json")
    loaded = DigitalTwinManager.from_json(path)
    assert loaded.get("fly-1").bookmarks["onset"] == "early"
    assert loaded.get("fly-branch").role == "Candidate"


def test_state_diff_and_temporal_explorer_use_existing_state_only():
    twin = _twin()
    manager = DigitalTwinManager()
    record = manager.register(twin)
    manager.snapshot(record.twin_id, "walk", time_s=1.0, bookmark="walk-bookmark")
    manager.snapshot(record.twin_id, "turn", time_s=2.0)
    explorer = TemporalExplorer()
    assert [state.state_label for state in explorer.select(record, behavior="Walk")] == ["Walk"]
    assert len(explorer.select(record, bookmark="walk-bookmark")) == 1
    assert [len(segment) for segment in explorer.segments(record)] == [1, 1, 1]
    diff = StateDiffEngine.compare(twin.history.entries[0], twin.history.entries[-1])
    assert "joint_angle" in diff.joint_changes
    assert "com_x" in diff.com_changes
    assert "trajectory_x" in diff.trajectory_changes


def test_scenario_graph_session_collaboration_and_platform_round_trip(tmp_path):
    workspace = ScenarioWorkspace()
    scenario = workspace.create("scenario-1", twin_ids=("fly-1",))
    workspace.add(scenario.scenario_id, "experiments", {"id": "experiment-1"})
    workspace.add(scenario.scenario_id, "observations", {"text": "caller observation"})
    workspace.add(scenario.scenario_id, "analyses", {"report": "existing-report"})
    workspace.add(scenario.scenario_id, "conclusions", {"status": "pending-review"})

    graph = KnowledgeGraph()
    graph.link("Dataset", "dataset-1", "Experiment", "experiment-1", "contains")
    graph.link("Experiment", "experiment-1", "Rollout", "rollout-1", "produces")
    graph.link("Rollout", "rollout-1", "DigitalFly", "fly-1", "materializes")
    assert len(graph.edges) == 3

    collaboration = CollaborationLayer()
    collaboration.comment("author", "Review this state", target="fly-1")
    collaboration.approve("reviewer", target="experiment-1", approved=False)
    collaboration.record_change("author", "added annotation", target="fly-1")
    assert len(collaboration.history) == 3

    platform = DigitalTwinPlatform()
    platform.twins.register(_twin(), role="Validation", source_rollout="rollout-1")
    platform.scenarios = workspace
    platform.graph = graph
    platform.collaboration = collaboration
    platform.add_session(VirtualLaboratorySession("session-1", camera={"preset": "front"}, timeline={"frame": 2}, opened_panels=("timeline",)))
    path = platform.to_json(tmp_path / "platform.json")
    loaded = DigitalTwinPlatform.from_json(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert loaded.twins.get("fly-1").role == "Validation"
    assert loaded.sessions["session-1"].timeline["frame"] == 2
    assert payload["scientific_scope"]


def test_invalid_role_and_unknown_graph_type_are_rejected():
    with pytest.raises(ValueError, match="unsupported twin role"):
        DigitalTwinManager().register(_twin(), role="Disease")
    with pytest.raises(ValueError, match="unsupported knowledge node type"):
        KnowledgeGraph().add_node("Unknown", "id")


def test_digital_twin_cli_validates_platform_json(tmp_path):
    platform = DigitalTwinPlatform()
    platform.twins.register(_twin(), role="Healthy", source_rollout="rollout-1")
    input_path = platform.to_json(tmp_path / "platform.json")
    output_path = tmp_path / "validation.json"
    assert digital_twin_cli(["validate", "--input", str(input_path), "--output", str(output_path)]) == 0
    assert json.loads(output_path.read_text(encoding="utf-8"))["overall_pass"] is True
