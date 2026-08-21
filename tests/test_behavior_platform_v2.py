from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.behavior_platform import (  # noqa: E402
    ComparisonCondition,
    ExportRequest,
    OfflineRenderResult,
    OfflineRenderRequest,
    RolloutData,
    build_comparison_playback_plan,
    build_viewer_plan,
    compare_rollouts,
    export_rollout_package,
    measure_rollout_behavior,
    render_offline,
)
import drosophila_pd.behavior_platform.rendering as rendering_module  # noqa: E402


def test_rollout_data_validates_arrays_and_metadata():
    rollout = _rollout("healthy")

    assert rollout.sample_count() == 6
    assert rollout.as_metadata()["condition_id"] == "healthy"
    assert np.allclose(rollout.time_s(), [0, 1, 2, 3, 4, 5])
    assert set(rollout.adhesion_arrays()) == {"LF", "RF"}
    assert set(rollout.joint_arrays()) == {"joint_a"}

    bad = RolloutData(
        condition_id="bad",
        timestep_s=1.0,
        thorax_positions=np.zeros((2, 2)),
        thorax_quaternions=_yaw_quaternions([0.0, 0.1]),
    )
    with pytest.raises(ValueError, match="thorax_positions"):
        bad.sample_count()


def test_rollout_data_optional_and_failure_paths():
    minimal = RolloutData(
        condition_id="minimal",
        timestep_s=0.5,
        thorax_positions=np.array([[0.0, 0.0, 1.0]]),
        thorax_quaternions=_yaw_quaternions([0.0]),
    )
    assert minimal.com_array() is None
    assert minimal.joint_arrays() == {}
    assert minimal.adhesion_arrays() == {}
    assert minimal.sample_count() == 1

    mapped = RolloutData.from_mapping(
        {
            "condition_id": "mapped",
            "sample_id": "seed1",
            "timestep_s": 1.0,
            "thorax_positions": [[0.0, 0.0, 1.0]],
            "thorax_quaternions": [[1.0, 0.0, 0.0, 0.0]],
            "metadata": {"seed": 1},
        }
    )
    assert mapped.as_metadata()["sample_id"] == "seed1"

    with pytest.raises(ValueError, match="timestep_s"):
        RolloutData(
            condition_id="bad_time",
            timestep_s=0.0,
            thorax_positions=np.zeros((1, 3)),
            thorax_quaternions=np.zeros((1, 4)),
        ).timestep()
    with pytest.raises(ValueError, match="sample counts"):
        RolloutData(
            condition_id="bad_quat_count",
            timestep_s=1.0,
            thorax_positions=np.zeros((2, 3)),
            thorax_quaternions=np.zeros((1, 4)),
        ).sample_count()
    with pytest.raises(ValueError, match="com_positions"):
        RolloutData(
            condition_id="bad_com",
            timestep_s=1.0,
            thorax_positions=np.zeros((2, 3)),
            thorax_quaternions=np.zeros((2, 4)),
            com_positions=np.zeros((1, 3)),
        ).sample_count()
    with pytest.raises(ValueError, match="joint_positions"):
        RolloutData(
            condition_id="bad_joint",
            timestep_s=1.0,
            thorax_positions=np.zeros((2, 3)),
            thorax_quaternions=np.zeros((2, 4)),
            joint_positions={"j": np.zeros((1,))},
        ).sample_count()
    with pytest.raises(ValueError, match="adhesion_outputs"):
        RolloutData(
            condition_id="bad_adhesion",
            timestep_s=1.0,
            thorax_positions=np.zeros((2, 3)),
            thorax_quaternions=np.zeros((2, 4)),
            adhesion_outputs={"LF": np.zeros((1,))},
        ).sample_count()
    with pytest.raises(ValueError, match="must contain finite samples"):
        RolloutData(
            condition_id="bad_mapping",
            timestep_s=1.0,
            thorax_positions=np.zeros((1, 3)),
            thorax_quaternions=np.zeros((1, 4)),
            adhesion_outputs={"LF": np.array(np.nan)},
        ).adhesion_arrays()


def test_measure_rollout_behavior_reports_complete_metric_surface():
    metrics = measure_rollout_behavior(
        _rollout("healthy"),
        config={
            "walking": {"speed_threshold_mm_s": 0.75},
            "freezing": {"immobility_speed_threshold_mm_s": 0.75},
            "turning": {"turn_rate_threshold_rad_s": 0.05},
            "open_field": {
                "arena_size_mm": [20.0, 20.0],
                "border_width_mm": 1.5,
                "grid_bins": 4,
            },
        },
    )

    assert metrics["behavior_platform_version"] == 2
    assert metrics["rollout"]["sample_count"] == 6
    assert np.isclose(metrics["trajectory"]["summary"]["path_length_mm"], 8.1231056256)
    assert metrics["walking_summary"]["bout_count"] == 1
    assert metrics["walking_summary"]["pause_count"] == 1
    assert metrics["walking_summary"]["walking_duty_cycle"] == 0.8
    assert metrics["freezing"]["freezing_episode_count"] == 1
    assert len(metrics["yaw_rate_rad_s"]) == 5
    assert metrics["turning_summary"]["turn_bout_count"] >= 1
    assert metrics["path_geometry"]["tortuosity"] > 1.0
    assert len(metrics["path_geometry"]["curvature_rad_per_mm"]) == 5
    assert metrics["exploration_metrics"]["available"] is True
    assert metrics["adhesion_summary"]["available"] is True
    assert metrics["joint_summary"]["joint_count"] == 1
    assert metrics["com_summary"]["available"] is True
    assert metrics["all_metrics_finite"] is True
    assert "biological" in metrics["scientific_scope"]


def test_measure_rollout_behavior_handles_disabled_open_field_and_no_optionals():
    stationary = RolloutData(
        condition_id="stationary",
        timestep_s=1.0,
        thorax_positions=np.array([[1.0, 1.0, 1.0], [1.0, 1.0, 1.0]]),
        thorax_quaternions=_yaw_quaternions([0.0, 0.0]),
    )

    metrics = measure_rollout_behavior(
        stationary,
        config={"open_field": {"enabled": False}},
    )

    assert metrics["exploration_metrics"]["available"] is False
    assert metrics["path_geometry"]["tortuosity"] is None
    assert metrics["adhesion_summary"]["available"] is False
    assert metrics["joint_summary"]["available"] is False
    assert metrics["com_summary"]["available"] is False
    assert metrics["path_geometry"]["mean_instantaneous_speed_mm_s"] == 0.0


def test_export_rollout_package_writes_csv_json_npz_and_png(tmp_path):
    result = export_rollout_package(
        _rollout("healthy"),
        ExportRequest(output_dir=tmp_path),
        measurement_config={"turning": {"turn_rate_threshold_rad_s": 0.05}},
    )

    assert set(result.files) == {
        "trajectory_csv",
        "behavior_json",
        "rollout_npz",
        "summary_png",
    }
    for path in result.files.values():
        assert path.exists()
        assert path.stat().st_size > 0
    assert result.files["trajectory_csv"].read_text(encoding="utf-8").splitlines()[0].startswith(
        "sample_index,time_s"
    )
    arrays = np.load(result.files["rollout_npz"])
    assert set(arrays.files) >= {
        "thorax_positions",
        "thorax_quaternions",
        "com_positions",
        "joint__joint_a",
        "adhesion__LF",
    }
    assert result.as_dict()["measurements_included"] is True

    with pytest.raises(FileExistsError):
        export_rollout_package(
            _rollout("healthy"),
            ExportRequest(output_dir=tmp_path, formats=("json",), overwrite=False),
        )


def test_export_rejects_unknown_format(tmp_path):
    with pytest.raises(ValueError, match="at least one"):
        export_rollout_package(
            _rollout("healthy"),
            ExportRequest(output_dir=tmp_path, formats=()),
        )
    with pytest.raises(ValueError, match="unsupported export formats"):
        export_rollout_package(
            _rollout("healthy"),
            ExportRequest(output_dir=tmp_path, formats=("pdf",)),
        )


def test_viewer_plan_describes_interactive_mujoco_features():
    plan = build_viewer_plan(_rollout("healthy")).as_dict()

    assert plan["viewer_type"] == "interactive_mujoco"
    assert {camera["name"] for camera in plan["camera_presets"]} == {
        "top",
        "side",
        "follow",
    }
    assert set(plan["overlays"]) == {
        "trajectory",
        "heading",
        "center_of_mass",
        "joint_state",
        "adhesion_state",
        "timeline",
    }
    assert "pause" in plan["controls"]
    assert "replay" in plan["controls"]


def test_offline_renderer_writes_png_sequence_for_single_and_comparison(tmp_path):
    single = render_offline(
        _rollout("healthy"),
        OfflineRenderRequest(output_dir=tmp_path / "single", stride=2),
    )
    assert single.format == "png_sequence"
    assert single.frame_count == 3
    assert all(path.exists() and path.stat().st_size > 0 for path in single.files)

    comparison = render_offline(
        [_rollout("healthy"), _rollout("candidate", x_scale=0.75)],
        OfflineRenderRequest(output_dir=tmp_path / "comparison", stride=3),
    )
    assert comparison.frame_count == 2
    assert all(path.name.endswith(".png") for path in comparison.files)
    assert comparison.as_dict()["frame_count"] == 2


def test_offline_renderer_validates_requests_and_animation_paths(tmp_path, monkeypatch):
    rollout = _rollout("healthy")
    with pytest.raises(ValueError, match="at least one rollout"):
        render_offline([], OfflineRenderRequest(output_dir=tmp_path / "empty"))
    with pytest.raises(ValueError, match="unsupported render format"):
        render_offline(rollout, OfflineRenderRequest(output_dir=tmp_path / "bad", format="webm"))
    with pytest.raises(ValueError, match="stride"):
        render_offline(rollout, OfflineRenderRequest(output_dir=tmp_path / "stride", stride=0))
    with pytest.raises(ValueError, match="fps"):
        render_offline(rollout, OfflineRenderRequest(output_dir=tmp_path / "fps", fps=0))

    def fake_encode_success(frame_paths, output_path, *, fps):
        output_path.write_bytes(b"fake animation")

    monkeypatch.setattr(rendering_module, "_encode_animation", fake_encode_success)
    gif = render_offline(
        rollout,
        OfflineRenderRequest(output_dir=tmp_path / "gif", format="gif", stride=3),
    )
    assert gif.files[0].name == "comparison.gif"
    assert gif.notes == ()

    def fake_encode_failure(frame_paths, output_path, *, fps):
        raise RuntimeError("encoder unavailable")

    monkeypatch.setattr(rendering_module, "_encode_animation", fake_encode_failure)
    mp4 = render_offline(
        rollout,
        OfflineRenderRequest(output_dir=tmp_path / "mp4", format="mp4", stride=3),
    )
    assert all(path.suffix == ".png" for path in mp4.files)
    assert "encoder unavailable" in mp4.notes[0]

    direct = OfflineRenderResult(
        format="png_sequence",
        files=(tmp_path / "a.png",),
        frame_count=1,
        backend="test",
    )
    assert direct.as_dict()["files"] == [str(tmp_path / "a.png")]


def test_comparison_viewer_and_metric_deltas_are_synchronized():
    healthy = ComparisonCondition("Healthy", _rollout("healthy"))
    candidate = ComparisonCondition("Candidate", _rollout("candidate", x_scale=0.75))
    rescue = ComparisonCondition("Rescue", _rollout("rescue", x_scale=0.9))

    report = compare_rollouts([healthy, candidate, rescue])
    assert report["comparison_version"] == 2
    assert report["baseline_role"] == "Healthy"
    assert report["synchronized_timeline"]["synchronized"] is True
    assert report["deltas_from_baseline"]["Candidate"]["delta_path_length_mm"] < 0
    assert report["deltas_from_baseline"]["Rescue"]["delta_path_length_mm"] < 0
    assert set(report["measurements"]) == {"Healthy", "Candidate", "Rescue"}

    plan = build_comparison_playback_plan([healthy, candidate, rescue]).as_dict()
    assert plan["layout"] == "side_by_side"
    assert plan["conditions"] == ["Healthy", "Candidate", "Rescue"]
    assert set(plan["viewer_plans"]) == {"Healthy", "Candidate", "Rescue"}
    assert ComparisonCondition("Healthy", _rollout("healthy"), "Unperturbed").label() == "Unperturbed"


def test_comparison_rejects_duplicate_roles():
    rollout = _rollout("healthy")
    with pytest.raises(ValueError, match="at least two"):
        compare_rollouts([ComparisonCondition("Healthy", rollout)])
    with pytest.raises(ValueError, match="unique"):
        compare_rollouts(
            [
                ComparisonCondition("Healthy", rollout),
                ComparisonCondition("Healthy", rollout),
            ]
        )


def _rollout(condition_id: str, *, x_scale: float = 1.0) -> RolloutData:
    positions = np.array(
        [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [2.0 * x_scale, 0.0, 1.0],
            [4.0 * x_scale, 0.5, 1.0],
            [6.0 * x_scale, 0.5, 1.0],
            [8.0 * x_scale, 0.0, 1.0],
        ],
        dtype=float,
    )
    return RolloutData(
        condition_id=condition_id,
        sample_id=f"{condition_id}_seed0",
        timestep_s=1.0,
        thorax_positions=positions,
        thorax_quaternions=_yaw_quaternions([0.0, 0.0, 0.2, 0.35, 0.2, 0.0]),
        com_positions=positions + np.array([0.0, 0.0, 0.1]),
        joint_positions={"joint_a": np.linspace(-1.0, 1.0, positions.shape[0])},
        adhesion_outputs={
            "LF": np.array([1, 1, 0, 0, 1, 1]),
            "RF": np.array([0, 1, 1, 0, 0, 1]),
        },
        metadata={"seed": 0},
    )


def _yaw_quaternions(yaws: list[float]) -> np.ndarray:
    return np.array(
        [[np.cos(yaw / 2.0), 0.0, 0.0, np.sin(yaw / 2.0)] for yaw in yaws],
        dtype=float,
    )
