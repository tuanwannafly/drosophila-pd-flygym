from __future__ import annotations

from pathlib import Path
import json
import sys

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.behavior_platform import (  # noqa: E402
    DigitalTwin,
    ExperimentRecord,
    InterventionDefinition,
    InterventionTimeline,
    LabLayout,
    ParameterSchedule,
    ScenarioDefinition,
    StagedIntervention,
    TwinConfiguration,
    TwinHistory,
    TwinMetadata,
    TwinScenario,
    TwinState,
    analyze_state_sequence,
    apply_intervention_parameters,
    batch_execute_scenarios,
    build_experiment_catalog,
    build_interactive_lab,
    build_scenario,
    classify_behavior_states,
    compare_intervention_reports,
    compare_scenarios,
    export_advanced_visualization_set,
    export_replay_dashboard,
    intervention_from_config,
    intervention_to_json,
    load_lab_layout,
    plot_behavioral_embeddings,
    plot_behavioral_network_graph,
    plot_behavioral_state_timeline,
    plot_intervention_timeline,
    plot_progression_map,
    plot_radar_plot,
    plot_sankey_transition_diagram,
    plot_similarity_heatmap,
    plot_trajectory_clusters,
    reconstruct_state_timeline,
    replay_intervention,
    save_lab_layout,
    scenario_report_to_json,
)


def test_digital_twin_serialization_snapshot_replay_and_scenarios(tmp_path):
    twin = _twin()
    assert twin.history.as_dict()["entry_count"] == 0
    twin = twin.record_state(TwinState(1.0, "Walk", {"speed": 2.0}, {"motor_scale": 1.0}))
    twin = twin.record_state(TwinState(0.0, "Idle", {"speed": 0.0}, {"motor_scale": 1.0}))
    scenario = TwinScenario(
        "candidate_scenario",
        "Candidate",
        TwinConfiguration("candidate", "1", {"motor_scale": 0.8}),
        TwinState(0.0, "Idle"),
    )
    twin = twin.add_scenario(scenario)

    assert [row["time_s"] for row in twin.reconstruct_timeline()] == [0.0, 1.0]
    assert twin.snapshot("latest").state.state_label == "Walk"
    assert twin.snapshot("early", time_s=0.5).state.state_label == "Idle"
    replay = twin.replay([0.0, 0.5, 1.5])
    assert [state.state_label for state in replay.states] == ["Idle", "Idle", "Walk"]
    assert replay.as_dict()["deterministic"] is True
    assert twin.as_dict()["digital_twin_version"] == 2
    assert "biological validation" in twin.as_dict()["scientific_scope"]

    output = twin.to_json(tmp_path / "twin.json")
    loaded = DigitalTwin.from_json(output)
    assert loaded.metadata.twin_id == "twin_a"
    assert loaded.scenarios[0].role == "Candidate"
    assert DigitalTwin.from_dict(twin.as_dict()).configuration.schema_version == "v2.digital_twin.1"

    with pytest.raises(ValueError, match="empty history"):
        _twin().snapshot("bad")
    with pytest.raises(ValueError, match="empty history"):
        _twin().replay([0.0])
    with pytest.raises(ValueError, match="no states"):
        TwinHistory().state_at(0.0)


def test_behavioral_state_machine_classification_and_reconstruction():
    labels = classify_behavior_states(
        speed_mm_s=[0.0, 0.5, 2.0, 2.0, 0.1, 1.2, 0.2],
        yaw_rate_rad_s=[0.0, 0.0, 0.1, 0.8, 0.0, 0.0, 0.0],
        radial_distance_mm=[0, 1, 2, 3, 8, 9, 1],
        recovery_mask=[False, False, False, False, False, True, False],
        custom_labels=[None, "CustomScan", None, None, None, None, None],
        config={"radial_explore_threshold_mm": 7.0},
    )
    assert labels == ["Pause", "CustomScan", "Walk", "Turn", "Explore", "Recover", "Pause"]

    report = analyze_state_sequence(labels, timestep_s=0.25, sequence_id="seq")
    assert report["transition_statistics"]["transition_count"] == 6
    assert report["state_durations_s"]["Pause"] == pytest.approx(0.5)
    assert report["episodes"][1]["behavior_type"] == "CustomScan"
    assert reconstruct_state_timeline(report)[0]["state"] == "Pause"
    assert report["transition_probabilities"]["Pause"]["CustomScan"] == pytest.approx(1.0)

    with pytest.raises(ValueError, match="at least one"):
        analyze_state_sequence([], timestep_s=0.1)
    with pytest.raises(ValueError, match="timestep_s"):
        analyze_state_sequence(["Walk"], timestep_s=0.0)
    with pytest.raises(ValueError, match="speed_mm_s"):
        classify_behavior_states(speed_mm_s=[float("nan")])
    with pytest.raises(ValueError, match="yaw_rate_rad_s"):
        classify_behavior_states(speed_mm_s=[1, 2], yaw_rate_rad_s=[1])
    with pytest.raises(ValueError, match="custom_labels"):
        classify_behavior_states(speed_mm_s=[1], custom_labels=["A", "B"])


def test_intervention_framework_schedule_replay_comparison_and_json(tmp_path):
    schedule = ParameterSchedule("motor_scale", (0.0, 10.0), (1.0, 0.8))
    step = ParameterSchedule("mode", (0.0, 1.0), ("a", "b"), interpolation="step")
    intervention = InterventionDefinition(
        "motor_axis_adjustment",
        {"coupling_scale": 0.75},
        schedules=(schedule, step),
    )

    assert schedule.value_at(5.0) == pytest.approx(0.9)
    assert step.value_at(0.5) == "a"
    params = apply_intervention_parameters({"motor_scale": 1.0, "coupling_scale": 1.0}, intervention, time_s=5.0)
    assert params["motor_scale"] == pytest.approx(0.9)
    assert params["coupling_scale"] == 0.75

    timeline = intervention_from_config(
        {
            "timeline_id": "interventions",
            "stages": [
                {
                    "stage_name": "Stage0",
                    "start_time_s": 0.0,
                    "intervention": intervention.as_dict(),
                },
                {
                    "stage_name": "Stage1",
                    "start_time_s": 10.0,
                    "intervention": {
                        "intervention_id": "late",
                        "parameter_modifications": {"motor_scale": 0.7},
                    },
                },
            ],
        }
    )
    replay = replay_intervention(timeline, base_parameters={"motor_scale": 1.0}, sample_times_s=[0.0, 5.0, 12.0])
    assert replay["replay"][2]["stage_name"] == "Stage1"
    assert "L-DOPA" in replay["scientific_scope"]
    output = intervention_to_json(timeline, tmp_path / "intervention.json")
    assert json.loads(output.read_text(encoding="utf-8"))["timeline_id"] == "interventions"

    comparison = compare_intervention_reports(
        {"metrics": {"speed": 1.0}, "missing": "x"},
        {"metrics": {"speed": 1.5}},
        metrics=("metrics.speed", "metrics.distance"),
    )
    assert comparison["metric_deltas"]["metrics.speed"]["delta"] == pytest.approx(0.5)
    assert comparison["metric_deltas"]["metrics.distance"]["delta"] is None

    with pytest.raises(ValueError, match="requires at least one"):
        ParameterSchedule("x", (), ()).value_at(0.0)
    with pytest.raises(ValueError, match="lengths"):
        ParameterSchedule("x", (0.0,), (1.0, 2.0)).value_at(0.0)
    with pytest.raises(ValueError, match="at least one stage"):
        intervention_from_config({"stages": []})


def test_intervention_config_from_json_path(tmp_path):
    config = {
        "timeline_id": "from_path",
        "stages": [
            {
                "stage_name": "Stage0",
                "start_time_s": 0.0,
                "intervention": {
                    "intervention_id": "identity",
                    "parameter_modifications": {"motor_scale": 1.0},
                },
            }
        ],
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    assert intervention_from_config(path).timeline_id == "from_path"


def test_interactive_lab_catalog_layout_save_load(tmp_path):
    catalog = build_experiment_catalog(
        [
            ExperimentRecord("exp0", "Healthy", {"report": "healthy.json"}, {"speed": 1.0}),
            {
                "experiment_id": "exp1",
                "condition": "Candidate",
                "artifacts": {"report": "candidate.json"},
                "metrics": {"speed": 0.8},
            },
        ]
    )
    lab = build_interactive_lab(catalog)
    assert "experiment_browser" in lab["layout"]["panels"]
    assert lab["layout"]["selected_conditions"] == ["Candidate", "Healthy"]

    layout = LabLayout("custom", ("metric_explorer",), ("Healthy",), {"metric": "speed"})
    path = save_lab_layout(layout, tmp_path / "tmp_layout.json")
    loaded = load_lab_layout(path)
    assert loaded.layout_id == "custom"
    assert loaded.filters["metric"] == "speed"


def test_scenario_engine_batch_comparison_and_json(tmp_path):
    healthy = build_scenario("healthy", role="Healthy", parameters={"motor_scale": 1.0})
    candidate = build_scenario("candidate", role="Candidate", parameters={"motor_scale": 0.8})
    assert isinstance(healthy, ScenarioDefinition)

    def executor(scenario):
        return {
            "speed": float(scenario.parameters["motor_scale"]),
            "label": scenario.role,
        }

    results = batch_execute_scenarios([healthy, candidate], executor)
    assert results[1].metadata["execution_order"] == 1
    report = compare_scenarios(results)
    assert report["deltas_from_baseline"]["candidate"]["speed"] == pytest.approx(-0.2)
    path = scenario_report_to_json(report, tmp_path / "scenario.json")
    assert path.exists()
    with pytest.raises(ValueError, match="at least two"):
        compare_scenarios(results[:1])


def test_advanced_visualization_exports_all_requested_outputs(tmp_path):
    state_report = analyze_state_sequence(["Pause", "Walk", "Turn", "Walk"], timestep_s=0.5)
    intervention = StagedIntervention(
        "Stage0",
        0.0,
        InterventionDefinition(
            "identity",
            {"motor_scale": 1.0},
            schedules=(ParameterSchedule("coupling_scale", (0.0, 1.0), (1.0, 0.8)),),
        ),
    )
    intervention_report = replay_intervention(
        timeline=InterventionTimeline("tl", (intervention,)),
        base_parameters={"motor_scale": 1.0, "coupling_scale": 1.0},
        sample_times_s=[0.0, 0.5, 1.0],
    )
    similarity_report = _similarity_report()

    files = export_advanced_visualization_set(
        state_report=state_report,
        intervention_report=intervention_report,
        similarity_report=similarity_report,
        output_dir=tmp_path,
        formats=("png", "svg", "pdf", "html"),
    )
    assert len(files) == 40
    assert all(path.exists() and path.stat().st_size > 0 for path in files.values())
    assert "Computational visualization" in files["replay_dashboard_html"].read_text(encoding="utf-8")

    extra_plotters = [
        plot_behavioral_state_timeline,
        plot_intervention_timeline,
        plot_sankey_transition_diagram,
        plot_behavioral_network_graph,
    ]
    for index, plotter in enumerate(extra_plotters):
        assert plotter(state_report if index != 1 else intervention_report, tmp_path / f"extra_{index}.png").exists()
    assert plot_radar_plot({"speed": 0.8, "turning": 0.4}, tmp_path / "radar.png").exists()
    assert plot_trajectory_clusters(similarity_report, tmp_path / "clusters.png").exists()
    assert plot_progression_map(intervention_report, tmp_path / "progression.png").exists()
    assert plot_similarity_heatmap(similarity_report, tmp_path / "heatmap.png").exists()
    assert plot_behavioral_embeddings(similarity_report, tmp_path / "embedding.png").exists()
    assert export_replay_dashboard(similarity_report, tmp_path / "dashboard.png").exists()

    with pytest.raises(ValueError, match="unsupported"):
        export_advanced_visualization_set(
            state_report=state_report,
            intervention_report=intervention_report,
            similarity_report=similarity_report,
            output_dir=tmp_path / "bad",
            formats=("docx",),
        )
    with pytest.raises(ValueError, match="at least one"):
        export_advanced_visualization_set(
            state_report=state_report,
            intervention_report=intervention_report,
            similarity_report=similarity_report,
            output_dir=tmp_path / "bad_empty",
            formats=(),
        )
    with pytest.raises(ValueError, match=".png, .svg, .pdf, or .html"):
        plot_similarity_heatmap(similarity_report, tmp_path / "bad.txt")


def _twin() -> DigitalTwin:
    return DigitalTwin(
        metadata=TwinMetadata("twin_a", git_commit="abc123", tags=("Session09",)),
        configuration=TwinConfiguration("config_a", "1.0", {"motor_scale": 1.0}),
    )


def _similarity_report() -> dict:
    return {
        "conditions": ["Healthy", "Candidate", "Future"],
        "metrics": {
            "trajectory_similarity": {
                "values": [[1.0, 0.8, 0.9], [0.8, 1.0, 0.85], [0.9, 0.85, 1.0]]
            },
            "gait_similarity": {
                "values": [[1.0, 0.7, 0.95], [0.7, 1.0, 0.8], [0.95, 0.8, 1.0]]
            },
        },
        "behavioral_similarity_matrix": {
            "values": [[1.0, 0.75, 0.92], [0.75, 1.0, 0.82], [0.92, 0.82, 1.0]]
        },
    }
