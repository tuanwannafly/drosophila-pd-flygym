from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.metrics.bouts import compute_walking_bout_metrics  # noqa: E402
from drosophila_pd.metrics.measurement_extension import (  # noqa: E402
    compute_extended_locomotion_metrics,
)
from drosophila_pd.metrics.open_field import compute_open_field_metrics  # noqa: E402
from drosophila_pd.metrics.trajectory import (  # noqa: E402
    compute_trajectory_timeseries,
    write_trajectory_csv,
)
from drosophila_pd.metrics.turning import compute_turning_metrics  # noqa: E402


def test_trajectory_timeseries_and_csv_export(tmp_path):
    positions = np.array(
        [
            [0.0, 0.0, 1.0],
            [1.0, 0.0, 1.0],
            [3.0, 0.0, 1.0],
            [6.0, 0.0, 1.0],
        ]
    )
    quaternions = _yaw_quaternions([0.0, 0.0, 0.0, 0.0])

    trajectory = compute_trajectory_timeseries(
        thorax_positions=positions,
        thorax_quaternions=quaternions,
        timestep_s=1.0,
    )

    assert trajectory["sample_count"] == 4
    assert trajectory["instantaneous_speed_mm_s"] == [0.0, 1.0, 2.0, 3.0]
    assert trajectory["step_speed_mm_s"] == [1.0, 2.0, 3.0]
    assert trajectory["cumulative_distance_mm"] == [0.0, 1.0, 3.0, 6.0]
    assert trajectory["summary"]["path_length_mm"] == 6.0

    output_path = write_trajectory_csv(trajectory, tmp_path / "trajectory.csv")
    lines = output_path.read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("sample_index,time_s,x_mm,y_mm")
    assert len(lines) == 5


def test_walking_bout_metrics_segment_walks_and_pauses():
    metrics = compute_walking_bout_metrics(
        step_speed_mm_s=np.array([2.0, 3.0, 0.0, 0.0, 4.0]),
        timestep_s=0.5,
        speed_threshold_mm_s=1.0,
    )

    assert metrics["bout_count"] == 2
    assert metrics["pause_count"] == 1
    assert metrics["walking_duration_s"] == 1.5
    assert metrics["pause_duration_s"] == 1.0
    assert metrics["walking_duty_cycle"] == 0.6
    assert metrics["walking_bouts"][0]["duration_s"] == 1.0
    assert metrics["walking_bouts"][1]["start_step"] == 4


def test_turning_metrics_report_yaw_rate_bouts_and_asymmetry():
    metrics = compute_turning_metrics(
        heading_rad=np.array([0.0, 0.1, 0.2, 0.2, -0.1]),
        timestep_s=1.0,
        turn_rate_threshold_rad_s=0.05,
    )

    assert metrics["yaw_rate_rad_s"] == [0.1, 0.1, 0.0, -0.30000000000000004]
    assert metrics["turn_bout_count"] == 2
    assert metrics["left_turn_bout_count"] == 1
    assert metrics["right_turn_bout_count"] == 1
    assert metrics["cumulative_turning_rad"] == 0.5
    assert np.isclose(metrics["left_right_asymmetry"], -0.2)


def test_open_field_metrics_use_declared_virtual_arena():
    positions = np.array(
        [
            [0.0, 0.0, 1.0],
            [4.0, 0.0, 1.0],
            [9.0, 0.0, 1.0],
            [-9.0, 0.0, 1.0],
        ]
    )

    metrics = compute_open_field_metrics(
        thorax_positions=positions,
        arena_center_xy_mm=[0.0, 0.0],
        arena_size_mm=[20.0, 20.0],
        center_fraction=0.5,
        border_width_mm=2.0,
        grid_bins=4,
    )

    assert metrics["available"] is True
    assert metrics["center_occupancy"] == 0.5
    assert metrics["border_occupancy"] == 0.5
    assert metrics["radial_distance_mm"]["mean"] == 5.5
    assert metrics["exploration_index"] > 0


def test_extended_locomotion_metrics_combines_analysis_without_open_field():
    positions = np.array(
        [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [2.0, 0.0, 1.0],
            [4.0, 0.0, 1.0],
        ]
    )
    quaternions = _yaw_quaternions([0.0, 0.0, 0.2, 0.4])

    metrics = compute_extended_locomotion_metrics(
        thorax_positions=positions,
        thorax_quaternions=quaternions,
        timestep_s=1.0,
        config={
            "walking_bouts": {"speed_threshold_mm_s": 1.0},
            "turning": {"turn_rate_threshold_rad_s": 0.1},
        },
    )

    assert metrics["measurement_extension_version"] == 1
    assert metrics["trajectory"]["summary"]["path_length_mm"] == 4.0
    assert metrics["walking_bout_metrics"]["bout_count"] == 1
    assert metrics["walking_bout_metrics"]["pause_count"] == 1
    assert metrics["turning_metrics"]["turn_bout_count"] == 1
    assert metrics["open_field_metrics"]["available"] is False
    assert "biological" in metrics["scientific_scope"]


def _yaw_quaternions(yaws: list[float]) -> np.ndarray:
    return np.array(
        [[np.cos(yaw / 2.0), 0.0, 0.0, np.sin(yaw / 2.0)] for yaw in yaws],
        dtype=float,
    )
