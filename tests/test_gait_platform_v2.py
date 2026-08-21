from __future__ import annotations

from pathlib import Path
import sys
import types

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.behavior_platform import (  # noqa: E402
    CANONICAL_LEG_ORDER,
    GaitAnalysisConfig,
    GaitAnimationRequest,
    GaitExportRequest,
    GaitInput,
    RolloutData,
    analyze_gait,
    export_gait_package,
    plot_contact_raster,
    plot_coordination_matrix,
    plot_foot_trajectories,
    plot_footfall_diagram,
    plot_gait_timeline,
    plot_joint_trajectories,
    plot_phase_wheel,
    plot_stride_plot,
    render_gait_animation,
    render_gait_visualization_set,
)
import drosophila_pd.behavior_platform.gait_animation as gait_animation_module  # noqa: E402


def test_gait_input_from_rollout_and_analysis_surface():
    rollout = _rollout()
    gait_input = GaitInput.from_rollout(rollout, foot_positions=_foot_positions())
    report = analyze_gait(gait_input)

    assert gait_input.sample_count() == 12
    assert report["gait_platform_version"] == 2
    assert report["leg_order"] == list(CANONICAL_LEG_ORDER)
    assert report["contact_analysis"]["duty_factor_by_leg"]["LF"] == pytest.approx(0.5)
    assert report["contact_analysis"]["transition_matrix_by_leg"]["LF"]["active_to_inactive"] == 3
    assert report["gait_analysis"]["stride_duration_s_by_leg"]["LF"]["count"] == 2
    assert report["gait_analysis"]["cadence_hz_by_leg"]["LF"] == pytest.approx(2 / 1.1)
    assert report["gait_analysis"]["stride_length_mm_by_leg"]["LF"]["mean"] is not None
    assert report["gait_analysis"]["gait_transition_detection"]["transition_count"] > 0
    assert report["gait_analysis"]["gait_entropy_bits"] > 0
    assert 0 <= report["gait_analysis"]["gait_stability"]["stability_index"] <= 1
    assert report["coordination_analysis"]["tripod_coordination"]["available"] is True
    assert report["coordination_analysis"]["tetrapod_coordination"]["tetrapod_samples"] >= 0
    assert "LF_to_RF" in report["coordination_analysis"]["inter_leg_phase"]
    assert "LF_RF" in report["coordination_analysis"]["cross_correlation"]
    assert report["joint_trajectory_summary"]["available"] is True
    assert report["foot_trajectory_summary"]["available"] is True
    assert report["all_metrics_finite"] is True
    assert "biological" in report["scientific_scope"]


def test_gait_input_validates_contact_foot_joint_and_config_errors():
    with pytest.raises(ValueError, match="at least one leg"):
        GaitInput(condition_id="bad", timestep_s=0.1, contact_states={}).sample_count()
    with pytest.raises(ValueError, match="sample counts"):
        GaitInput(
            condition_id="bad",
            timestep_s=0.1,
            contact_states={"LF": [1, 0], "RF": [1]},
        ).sample_count()
    with pytest.raises(ValueError, match="timestep_s"):
        GaitInput(condition_id="bad", timestep_s=0.0, contact_states={"LF": [1]}).timestep()
    with pytest.raises(ValueError, match="foot_positions"):
        GaitInput(
            condition_id="bad",
            timestep_s=0.1,
            contact_states={"LF": [1, 0]},
            foot_positions={"LF": np.zeros((2, 2))},
        ).sample_count()
    with pytest.raises(ValueError, match="joint_trajectories"):
        GaitInput(
            condition_id="bad",
            timestep_s=0.1,
            contact_states={"LF": [1, 0]},
            joint_trajectories={"j": np.array(np.nan)},
        ).sample_count()
    with pytest.raises(ValueError, match="contact_source"):
        GaitInput.from_rollout(_rollout(), contact_source="force")
    with pytest.raises(ValueError, match="no adhesion_outputs"):
        GaitInput.from_rollout(
            RolloutData(
                condition_id="no_adhesion",
                timestep_s=0.1,
                thorax_positions=np.zeros((2, 3)),
                thorax_quaternions=_yaw_quaternions([0.0, 0.0]),
            )
        )


def test_gait_analysis_supports_partial_leg_sets_and_config_mapping():
    gait_input = GaitInput(
        condition_id="two_leg",
        timestep_s=0.5,
        contact_states={"LF": [1, 1, 0, 0], "RF": [0, 0, 1, 1]},
    )
    report = analyze_gait(
        gait_input,
        config={"contact_threshold": 0.4, "min_stride_duration_s": 0.0},
    )

    assert report["leg_order"] == ["LF", "RF"]
    assert report["coordination_analysis"]["tripod_coordination"]["available"] is False
    assert report["contact_analysis"]["contact_symmetry"]["LF_RF"]["duty_factor_delta_left_minus_right"] == 0
    assert report["coordination_analysis"]["coordination_matrix"]["correlation"][0][1] == pytest.approx(-1)
    assert GaitAnalysisConfig(contact_threshold=0.25).contact_threshold == 0.25


def test_gait_export_writes_json_csv_npz_png_and_svg(tmp_path):
    gait_input = GaitInput.from_rollout(_rollout(), foot_positions=_foot_positions())
    result = export_gait_package(
        gait_input,
        GaitExportRequest(output_dir=tmp_path, formats=("csv", "json", "npz", "png", "svg")),
    )

    expected = {
        "gait_analysis_json",
        "contact_timeline_csv",
        "stride_events_csv",
        "duty_factor_csv",
        "gait_arrays_npz",
        "footfall_png",
        "contact_raster_png",
        "gait_timeline_png",
        "coordination_matrix_png",
        "phase_wheel_png",
        "stride_plot_png",
        "joint_trajectories_png",
        "foot_trajectories_png",
        "footfall_svg",
        "contact_raster_svg",
        "gait_timeline_svg",
        "coordination_matrix_svg",
        "phase_wheel_svg",
        "stride_plot_svg",
        "joint_trajectories_svg",
        "foot_trajectories_svg",
    }
    assert set(result.files) == expected
    assert result.as_dict()["analysis_included"] is True
    for path in result.files.values():
        assert path.exists()
        assert path.stat().st_size > 0
    arrays = np.load(result.files["gait_arrays_npz"])
    assert set(arrays.files) >= {"time_s", "contact_matrix", "foot__LF", "joint__joint_a"}
    assert result.files["contact_timeline_csv"].read_text(encoding="utf-8").startswith(
        "sample_index,time_s"
    )

    with pytest.raises(FileExistsError):
        export_gait_package(
            gait_input,
            GaitExportRequest(output_dir=tmp_path, formats=("json",), overwrite=False),
        )
    with pytest.raises(ValueError, match="unsupported gait export formats"):
        export_gait_package(gait_input, GaitExportRequest(output_dir=tmp_path, formats=("pdf",)))
    with pytest.raises(ValueError, match="at least one"):
        export_gait_package(gait_input, GaitExportRequest(output_dir=tmp_path, formats=()))


def test_individual_gait_visualizations_validate_suffix_and_write_files(tmp_path):
    gait_input = GaitInput.from_rollout(_rollout(), foot_positions=_foot_positions())
    report = analyze_gait(gait_input)
    plotters = [
        plot_footfall_diagram,
        plot_contact_raster,
        plot_gait_timeline,
        plot_coordination_matrix,
        plot_phase_wheel,
        plot_stride_plot,
        plot_joint_trajectories,
        plot_foot_trajectories,
    ]
    for index, plotter in enumerate(plotters):
        path = plotter(gait_input, report, tmp_path / f"plot_{index}.png")
        assert path.exists()
        assert path.stat().st_size > 0

    svg_files = render_gait_visualization_set(
        gait_input,
        tmp_path / "svg",
        analysis=report,
        formats=("svg",),
    )
    assert all(path.suffix == ".svg" for path in svg_files.values())
    with pytest.raises(ValueError, match=".png or .svg"):
        plot_footfall_diagram(gait_input, report, tmp_path / "bad.pdf")
    with pytest.raises(ValueError, match="unsupported visualization format"):
        render_gait_visualization_set(gait_input, tmp_path / "bad", formats=("pdf",))


def test_gait_animation_png_sequence_and_encoder_paths(tmp_path, monkeypatch):
    gait_input = GaitInput.from_rollout(_rollout(), foot_positions=_foot_positions())
    png = render_gait_animation(
        gait_input,
        GaitAnimationRequest(output_dir=tmp_path / "png", stride=4),
    )
    assert png.format == "png_sequence"
    assert png.frame_count == 3
    assert all(path.exists() and path.stat().st_size > 0 for path in png.files)

    def fake_success(frame_paths, output_path, *, fps):
        assert fps == 12
        output_path.write_bytes(b"fake gif")

    monkeypatch.setattr(gait_animation_module, "_encode_animation", fake_success)
    gif = render_gait_animation(
        [gait_input, _candidate_gait_input()],
        GaitAnimationRequest(output_dir=tmp_path / "gif", format="gif", fps=12, stride=6),
    )
    assert gif.files[0].name == "gait.gif"
    assert gif.notes == ()
    assert gif.as_dict()["frame_count"] == 2

    def fake_failure(frame_paths, output_path, *, fps):
        raise RuntimeError("no encoder")

    monkeypatch.setattr(gait_animation_module, "_encode_animation", fake_failure)
    mp4 = render_gait_animation(
        gait_input,
        GaitAnimationRequest(output_dir=tmp_path / "mp4", format="mp4", stride=6),
    )
    assert all(path.suffix == ".png" for path in mp4.files)
    assert "no encoder" in mp4.notes[0]

    with pytest.raises(ValueError, match="at least one"):
        render_gait_animation([], GaitAnimationRequest(output_dir=tmp_path / "empty"))
    with pytest.raises(ValueError, match="unsupported"):
        render_gait_animation(gait_input, GaitAnimationRequest(output_dir=tmp_path / "bad", format="webm"))
    with pytest.raises(ValueError, match="fps"):
        render_gait_animation(gait_input, GaitAnimationRequest(output_dir=tmp_path / "fps", fps=0))
    with pytest.raises(ValueError, match="stride"):
        render_gait_animation(gait_input, GaitAnimationRequest(output_dir=tmp_path / "stride", stride=0))


def test_gait_animation_internal_encoder_success_path(tmp_path, monkeypatch):
    fake_imageio = types.ModuleType("imageio")
    fake_imageio.__path__ = []
    fake_v2 = types.ModuleType("imageio.v2")

    def fake_imread(path):
        return np.zeros((2, 2, 3), dtype=np.uint8)

    def fake_mimsave(output_path, frames, *, fps):
        assert len(frames) == 1
        assert fps == 9
        Path(output_path).write_bytes(b"encoded")

    fake_v2.imread = fake_imread
    fake_v2.mimsave = fake_mimsave
    monkeypatch.setitem(sys.modules, "imageio", fake_imageio)
    monkeypatch.setitem(sys.modules, "imageio.v2", fake_v2)

    output = tmp_path / "encoded.gif"
    gait_animation_module._encode_animation([tmp_path / "frame.png"], output, fps=9)

    assert output.read_bytes() == b"encoded"


def _rollout() -> RolloutData:
    positions = np.column_stack(
        [
            np.linspace(0.0, 11.0, 12),
            np.sin(np.linspace(0.0, 1.2, 12)) * 0.5,
            np.ones(12),
        ]
    )
    contacts = {
        "LF": [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        "RM": [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        "LH": [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        "RF": [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
        "LM": [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
        "RH": [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
    }
    return RolloutData(
        condition_id="healthy",
        sample_id="seed0",
        timestep_s=0.1,
        thorax_positions=positions,
        thorax_quaternions=_yaw_quaternions(np.linspace(0.0, 0.4, 12)),
        joint_positions={"joint_a": np.linspace(-0.5, 0.5, 12)},
        adhesion_outputs=contacts,
        metadata={"seed": 0},
    )


def _candidate_gait_input() -> GaitInput:
    data = GaitInput.from_rollout(_rollout(), foot_positions=_foot_positions())
    contacts = {leg: np.roll(values, 1) for leg, values in data.contact_arrays().items()}
    return GaitInput(
        condition_id="candidate",
        sample_id="seed0",
        timestep_s=data.timestep_s,
        contact_states=contacts,
        foot_positions=data.foot_positions,
        joint_trajectories=data.joint_trajectories,
        metadata=data.metadata,
    )


def _foot_positions() -> dict[str, np.ndarray]:
    base = np.column_stack(
        [
            np.linspace(0.0, 6.0, 12),
            np.zeros(12),
            np.zeros(12),
        ]
    )
    return {
        leg: base + np.array([0.0, offset, 0.0])
        for leg, offset in zip(CANONICAL_LEG_ORDER, [-1.5, -1.0, -0.5, 0.5, 1.0, 1.5])
    }


def _yaw_quaternions(yaws) -> np.ndarray:
    return np.array(
        [[np.cos(float(yaw) / 2.0), 0.0, 0.0, np.sin(float(yaw) / 2.0)] for yaw in yaws],
        dtype=float,
    )
