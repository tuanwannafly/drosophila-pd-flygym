from __future__ import annotations

from pathlib import Path
import json
import sys
import types

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.behavior_platform import (  # noqa: E402
    Arena,
    ArenaZone,
    BehaviorEpisode,
    BehaviorReport,
    BehaviorSequence,
    ProgressionStage,
    ProgressionTimeline,
    SynchronizedPlaybackRequest,
    analyze_open_field,
    build_behavior_dashboard,
    compare_behavior_conditions,
    export_behavior_dashboard,
    export_open_field_report,
    interpolate_stages,
    interpolated_stage_at,
    plot_trajectory_explorer,
    progression_from_config,
    progression_to_json,
    render_synchronized_playback,
    replay_progression,
    stage_at,
)
from drosophila_pd.behavior_platform.rollout import RolloutData  # noqa: E402
import drosophila_pd.behavior_platform.video_system as video_module  # noqa: E402


def test_data_models_serialize_core_session07_session08_types():
    episode = BehaviorEpisode("ep1", "walking", 0.2, 1.0, {"source": "synthetic"})
    sequence = BehaviorSequence("seq1", [episode])
    zone = ArenaZone("roi", "circle", radius_mm=2.0)
    arena = Arena.circular(radius_mm=8.0, zones=(zone,))
    stage = ProgressionStage("Stage0", 0, {"motor_scale": 1.0})
    timeline = ProgressionTimeline("tl", [stage], [0.0])
    report = BehaviorReport("report", {"open_field": {"center": 0.5}})

    assert episode.duration_s == pytest.approx(0.8)
    assert sequence.as_dict()["episode_count"] == 1
    assert arena.as_dict()["shape"] == "circle"
    assert arena.as_dict()["zones"][0]["name"] == "roi"
    assert timeline.as_dict()["stages"][0]["name"] == "Stage0"
    assert report.as_dict()["sections"]["open_field"]["center"] == 0.5


def test_open_field_rectangular_and_circular_metrics_and_exports(tmp_path):
    rollout = _rollout("healthy")
    arena = Arena.rectangular(
        size_xy_mm=(12.0, 12.0),
        border_width_mm=2.0,
        center_fraction=0.4,
        zones=(ArenaZone("food_roi", "rectangle", center_xy_mm=(2.0, 0.0), size_xy_mm=(3.0, 3.0)),),
    )
    report = analyze_open_field(rollout, arena, grid_bins=4)

    assert report["open_field_version"] == 2
    assert report["center_occupancy"] > 0
    assert report["border_occupancy"] >= 0
    assert report["exploration_index"] > 0
    assert report["heat_map"]["grid_bins"] == 4
    assert report["transition_probability_matrix"]["zones"]
    assert report["zone_transition_graph"]
    assert report["exploration_entropy_bits"] > 0
    assert report["coverage_ratio"] == report["exploration_index"]
    assert report["revisit_frequency_hz"] >= 0
    assert report["path_tortuosity"] is not None
    assert "food_roi" in report["custom_zone_occupancy"]
    assert report["all_metrics_finite"] is True

    circular = analyze_open_field(_rollout("candidate", scale=0.8), Arena.circular(radius_mm=8.0), grid_bins=5)
    assert circular["arena"]["shape"] == "circle"
    assert circular["radial_distance_mm"]["max"] <= 8.0

    files = export_open_field_report(report, tmp_path, formats=("json", "csv"))
    assert files["json"].exists()
    assert files["radial_csv"].read_text(encoding="utf-8").startswith("sample_index")
    with pytest.raises(ValueError, match="unsupported"):
        export_open_field_report(report, tmp_path / "bad", formats=("pdf",))


def test_open_field_validation_errors():
    rollout = _rollout("healthy")
    with pytest.raises(ValueError, match="grid_bins"):
        analyze_open_field(rollout, Arena.rectangular(), grid_bins=0)
    with pytest.raises(ValueError, match="unsupported arena shape"):
        analyze_open_field(rollout, Arena(arena_id="bad", shape="triangle"))
    with pytest.raises(ValueError, match="radius_mm"):
        analyze_open_field(rollout, Arena.circular(radius_mm=0.0))
    with pytest.raises(ValueError, match="center_fraction"):
        analyze_open_field(rollout, Arena.rectangular(center_fraction=1.5))
    with pytest.raises(ValueError, match="rectangular ArenaZone"):
        analyze_open_field(
            rollout,
            Arena.rectangular(zones=(ArenaZone("bad", "rectangle", size_xy_mm=(-1.0, 2.0)),)),
        )


def test_progression_engine_config_interpolation_replay_and_json(tmp_path):
    config = {
        "timeline_id": "stages",
        "stages": [
            {"name": "Stage0", "computational_parameters": {"motor_scale": 1.0, "label": "a"}},
            {"name": "Stage1", "computational_parameters": {"motor_scale": 0.8, "label": "b"}},
            {"name": "Stage2", "computational_parameters": {"motor_scale": 0.6, "label": "c"}},
        ],
        "stage_times_s": [0.0, 10.0, 20.0],
        "metadata": {"seed": 7},
    }
    config_path = tmp_path / "progression.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    timeline = progression_from_config(config_path)
    assert stage_at(timeline, 11.0).name == "Stage1"
    mid = interpolated_stage_at(timeline, 5.0)
    assert mid.computational_parameters["motor_scale"] == pytest.approx(0.9)
    assert mid.computational_parameters["label"] in {"a", "b"}
    manual = interpolate_stages(timeline.stages[0], timeline.stages[1], 0.25)
    assert manual.computational_parameters["motor_scale"] == pytest.approx(0.95)
    replay = replay_progression(timeline, sample_times_s=[0.0, 5.0, 20.0])
    assert len(replay["replayed_stages"]) == 3
    assert "biological disease" in replay["scientific_scope"]
    output = progression_to_json(timeline, tmp_path / "timeline.json")
    assert json.loads(output.read_text(encoding="utf-8"))["timeline_id"] == "stages"

    same = progression_from_config(config)
    assert same.as_dict()["metadata"]["seed"] == 7
    with pytest.raises(ValueError, match="at least one"):
        progression_from_config({"stages": [], "stage_times_s": []})
    with pytest.raises(ValueError, match="length"):
        progression_from_config({"stages": [{"name": "Stage0"}], "stage_times_s": [0, 1]})
    with pytest.raises(ValueError, match="sorted"):
        progression_from_config(
            {
                "stages": [{"name": "Stage0"}, {"name": "Stage1"}],
                "stage_times_s": [1, 0],
            }
        )


def test_multi_condition_behavior_comparison_reports_similarity(tmp_path):
    healthy = analyze_open_field(_rollout("Healthy"), Arena.rectangular(size_xy_mm=(12.0, 12.0)), grid_bins=4)
    candidate = analyze_open_field(_rollout("Candidate", scale=0.75), Arena.rectangular(size_xy_mm=(12.0, 12.0)), grid_bins=4)
    stage = dict(candidate)
    stage["gait_analysis"] = {"gait_stability": {"stability_index": 0.8, "support_count_std": 0.2}}
    stage["turning_summary"] = {"cumulative_turning_rad": 0.4}

    comparison = compare_behavior_conditions(
        {"Healthy": healthy, "Candidate": candidate, "Stage1": stage},
        output_path=tmp_path / "comparison.json",
    )

    assert comparison["behavior_comparison_version"] == 2
    assert comparison["conditions"] == ["Healthy", "Candidate", "Stage1"]
    assert comparison["metrics"]["trajectory_similarity"]["values"][0][0] == pytest.approx(1.0)
    assert comparison["metrics"]["dtw_distance"]["values"][0][1] >= 0
    assert comparison["metrics"]["frechet_distance"]["values"][0][1] >= 0
    assert comparison["behavioral_similarity_matrix"]["values"][0][0] == pytest.approx(1.0)
    assert (tmp_path / "comparison.json").exists()
    with pytest.raises(ValueError, match="at least two"):
        compare_behavior_conditions({"Healthy": healthy})
    with pytest.raises(ValueError, match="trajectory"):
        compare_behavior_conditions({"A": {}, "B": {}})


def test_behavior_comparison_accepts_alternate_report_shapes():
    report_a = {
        "trajectory": {
            "x_mm": [0.0, 1.0, 2.0],
            "y_mm": [0.0, 0.5, 0.0],
        },
        "open_field": {"heat_map": {"counts": [[1, 0], [0, 1]]}},
        "turning": {"yaw_rate": [0.0, "ignored", 1.0]},
        "gait_analysis": {"gait_stability": {"values": [1.0, 0.5]}},
    }
    report_b = {
        "trajectory": {
            "x_mm": [0.0, 1.2, 2.4],
            "y_mm": [0.0, 0.4, 0.0],
        },
        "heat_map": {"counts": [[1, 1, 0], [0, 1, 0], [0, 0, 1]]},
        "turning_summary": {"cumulative_turning_rad": 0.2},
        "center_occupancy": 0.25,
        "border_occupancy": 0.5,
        "exploration_entropy_bits": 1.0,
        "coverage_ratio": 0.75,
    }

    comparison = compare_behavior_conditions({"A": report_a, "B": report_b})

    assert comparison["metrics"]["occupancy_similarity"]["values"][0][1] >= 0.0
    assert comparison["metrics"]["trajectory_similarity"]["values"][0][1] < 1.0
    assert comparison["metrics"]["gait_similarity"]["values"][0][1] > 0.0


def test_dashboard_and_trajectory_visualization_exports(tmp_path):
    reports = {
        "Healthy": analyze_open_field(_rollout("Healthy"), Arena.rectangular(size_xy_mm=(12.0, 12.0)), grid_bins=4),
        "Candidate": analyze_open_field(_rollout("Candidate", scale=0.7), Arena.rectangular(size_xy_mm=(12.0, 12.0)), grid_bins=4),
    }
    dashboard = build_behavior_dashboard(reports)
    assert "trajectory_explorer" in dashboard["dashboard"]["panels"]
    assert dashboard["dashboard"]["filters"]["time_slider"] is True

    files = export_behavior_dashboard(reports, tmp_path / "dashboard", formats=("png", "svg", "pdf", "html"))
    assert set(files) == {"png", "svg", "pdf", "html"}
    assert all(path.exists() and path.stat().st_size > 0 for path in files.values())
    assert "Computational visualization" in files["html"].read_text(encoding="utf-8")
    trajectory = plot_trajectory_explorer(
        {"Healthy": _rollout("Healthy"), "Candidate": _rollout("Candidate", scale=0.7)},
        tmp_path / "trajectory.png",
    )
    assert trajectory.exists()
    with pytest.raises(ValueError, match="unsupported"):
        export_behavior_dashboard(reports, tmp_path / "bad", formats=("docx",))


def test_synchronized_video_png_sequence_and_encoder_paths(tmp_path, monkeypatch):
    rollouts = {"Healthy": _rollout("Healthy"), "Candidate": _rollout("Candidate", scale=0.8)}
    png = render_synchronized_playback(
        rollouts,
        SynchronizedPlaybackRequest(output_dir=tmp_path / "png", stride=4),
    )
    assert png.format == "png_sequence"
    assert png.frame_count == 3
    assert all(path.exists() and path.stat().st_size > 0 for path in png.files)

    def fake_success(frame_paths, output_path, *, fps):
        assert fps == 10
        output_path.write_bytes(b"movie")

    monkeypatch.setattr(video_module, "_encode_animation", fake_success)
    gif = render_synchronized_playback(
        rollouts,
        SynchronizedPlaybackRequest(output_dir=tmp_path / "gif", format="gif", fps=10, stride=6),
    )
    assert gif.files[0].name == "behavior_playback.gif"
    assert gif.notes == ()

    def fake_failure(frame_paths, output_path, *, fps):
        raise RuntimeError("encoder missing")

    monkeypatch.setattr(video_module, "_encode_animation", fake_failure)
    mp4 = render_synchronized_playback(
        rollouts,
        SynchronizedPlaybackRequest(output_dir=tmp_path / "mp4", format="mp4", stride=6),
    )
    assert all(path.suffix == ".png" for path in mp4.files)
    assert "encoder missing" in mp4.notes[0]

    with pytest.raises(ValueError, match="at least two"):
        render_synchronized_playback({"Healthy": _rollout("Healthy")}, SynchronizedPlaybackRequest(output_dir=tmp_path))
    with pytest.raises(ValueError, match="unsupported"):
        render_synchronized_playback(rollouts, SynchronizedPlaybackRequest(output_dir=tmp_path, format="webm"))
    with pytest.raises(ValueError, match="fps"):
        render_synchronized_playback(rollouts, SynchronizedPlaybackRequest(output_dir=tmp_path, fps=0))
    with pytest.raises(ValueError, match="stride"):
        render_synchronized_playback(rollouts, SynchronizedPlaybackRequest(output_dir=tmp_path, stride=0))


def test_video_internal_encoder_success_path(tmp_path, monkeypatch):
    fake_imageio = types.ModuleType("imageio")
    fake_imageio.__path__ = []
    fake_v2 = types.ModuleType("imageio.v2")

    def fake_imread(path):
        return np.zeros((2, 2, 3), dtype=np.uint8)

    def fake_mimsave(output_path, frames, *, fps):
        assert fps == 8
        assert len(frames) == 1
        Path(output_path).write_bytes(b"encoded")

    fake_v2.imread = fake_imread
    fake_v2.mimsave = fake_mimsave
    monkeypatch.setitem(sys.modules, "imageio", fake_imageio)
    monkeypatch.setitem(sys.modules, "imageio.v2", fake_v2)

    output = tmp_path / "encoded.gif"
    video_module._encode_animation([tmp_path / "frame.png"], output, fps=8)
    assert output.read_bytes() == b"encoded"


def _rollout(condition_id: str, *, scale: float = 1.0) -> RolloutData:
    t = np.linspace(0.0, 1.0, 12)
    positions = np.column_stack(
        [
            scale * np.linspace(-4.0, 4.0, 12),
            np.sin(t * 2 * np.pi) * 2.0,
            np.ones(12),
        ]
    )
    return RolloutData(
        condition_id=condition_id,
        sample_id=f"{condition_id}_seed0",
        timestep_s=0.1,
        thorax_positions=positions,
        thorax_quaternions=_yaw_quaternions(np.linspace(0.0, 0.5, 12)),
        metadata={"seed": 0},
    )


def _yaw_quaternions(yaws) -> np.ndarray:
    return np.array(
        [[np.cos(float(yaw) / 2.0), 0.0, 0.0, np.sin(float(yaw) / 2.0)] for yaw in yaws],
        dtype=float,
    )
