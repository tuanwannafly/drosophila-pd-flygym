from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.experiments.candidate_robustness import (  # noqa: E402
    REQUIRED_E3_DURATION_S,
    REQUIRED_E3_SEEDS,
    load_candidate_robustness_config,
)
from drosophila_pd.experiments.healthy_baseline import (  # noqa: E402
    HealthyBaselineConfig,
)
from drosophila_pd.experiments.measurement_refresh import (  # noqa: E402
    G7_EXPERIMENT_ID,
    RolloutArrays,
    build_measurement_refresh_report,
    build_measurement_refresh_unavailable_report,
    export_rollout_artifacts,
    load_measurement_extension_config,
)
from drosophila_pd.metrics.measurement_extension import (  # noqa: E402
    compute_extended_locomotion_metrics,
)


def test_g7_uses_frozen_e3_candidate_seed_and_duration_config():
    config = load_candidate_robustness_config(
        REPO_ROOT / "configs" / "experiments" / "validation" / "milestone_e3.yaml"
    )

    assert config.seeds == REQUIRED_E3_SEEDS
    assert config.duration_s == REQUIRED_E3_DURATION_S
    assert config.candidate.motor_scale == 0.8
    assert config.candidate.coupling_scale == 0.75


def test_measurement_extension_config_merges_defaults_and_strips_metadata(tmp_path):
    config_path = tmp_path / "g5.yaml"
    config_path.write_text(
        "\n".join(
            [
                "schema_version: 1",
                "phase: G5",
                "walking_bouts:",
                "  speed_threshold_mm_s: 2.5",
            ]
        ),
        encoding="utf-8",
    )

    config = load_measurement_extension_config(config_path)

    assert config["walking_bouts"]["speed_threshold_mm_s"] == 2.5
    assert config["walking_bouts"]["min_bout_duration_s"] == 0.0
    assert config["turning"]["turn_rate_threshold_rad_s"] == 0.5
    assert "phase" not in config


def test_export_rollout_artifacts_writes_required_g7_files(tmp_path):
    arrays = _synthetic_rollout_arrays()
    measurement = compute_extended_locomotion_metrics(
        thorax_positions=arrays.thorax_positions,
        thorax_quaternions=arrays.thorax_quaternions,
        timestep_s=arrays.timestep_s,
        config={
            "walking_bouts": {"speed_threshold_mm_s": 1.0},
            "turning": {"turn_rate_threshold_rad_s": 0.05},
        },
    )

    artifacts = export_rollout_artifacts(
        condition_dir=tmp_path / "seed_0" / "baseline",
        arrays=arrays,
        measurement_report=measurement,
    )

    expected_keys = {
        "raw_rollout_arrays_npz",
        "trajectory_csv",
        "heading_csv",
        "instantaneous_speed_csv",
        "yaw_rate_csv",
        "walking_bouts_csv",
        "pause_bouts_csv",
        "turn_bouts_csv",
        "g5_measurements_json",
    }
    assert set(artifacts) == expected_keys
    assert all(Path(path).exists() for path in artifacts.values())

    raw = np.load(artifacts["raw_rollout_arrays_npz"])
    assert raw["thorax_positions_mm"].shape == (4, 3)
    assert raw["thorax_quaternions"].shape == (4, 4)
    assert raw["timestep_s"][0] == 1.0
    assert Path(artifacts["trajectory_csv"]).read_text(encoding="utf-8").splitlines()[
        0
    ].startswith("sample_index,time_s,x_mm")
    assert "duration_s" in Path(artifacts["walking_bouts_csv"]).read_text(
        encoding="utf-8"
    ).splitlines()[0]


def test_build_measurement_refresh_report_records_scope_and_artifact_counts(tmp_path):
    validation_config = load_candidate_robustness_config(
        REPO_ROOT / "configs" / "experiments" / "validation" / "milestone_e3.yaml"
    )
    pair = _synthetic_completed_pair(tmp_path)
    report = build_measurement_refresh_report(
        baseline_config=HealthyBaselineConfig.from_mapping({}),
        validation_config=validation_config,
        measurement_config=load_measurement_extension_config(None),
        output_dir=tmp_path,
        pairs=[pair],
        repo_root=REPO_ROOT,
    )

    assert report["experiment_id"] == G7_EXPERIMENT_ID
    assert report["frozen_inputs"]["candidate_motor_scale"] == 0.8
    assert report["frozen_inputs"]["candidate_coupling_scale"] == 0.75
    assert report["artifact_inventory"]["artifact_counts"][
        "raw_rollout_arrays_npz"
    ] == 2
    assert report["checks"]["frozen_seed_set_preserved"]["pass"] is True
    assert report["checks"]["all_seed_pairs_completed"]["pass"] is False
    assert "not tune" in report["scientific_scope"]


def test_unavailable_report_does_not_claim_pass(tmp_path):
    validation_config = load_candidate_robustness_config(
        REPO_ROOT / "configs" / "experiments" / "validation" / "milestone_e3.yaml"
    )
    report = build_measurement_refresh_unavailable_report(
        RuntimeError("FlyGym unavailable"),
        baseline_config=HealthyBaselineConfig.from_mapping({}),
        validation_config=validation_config,
        measurement_config=load_measurement_extension_config(None),
        output_dir=tmp_path,
        repo_root=REPO_ROOT,
    )

    assert report["overall_pass"] is False
    assert report["local_execution"] == "NOT VERIFIED"
    assert report["error_type"] == "RuntimeError"


def _synthetic_rollout_arrays() -> RolloutArrays:
    positions = np.array(
        [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, 1.0],
            [2.0, 0.0, 1.0],
            [4.0, 1.0, 1.0],
        ]
    )
    return RolloutArrays(
        thorax_positions=positions,
        thorax_quaternions=_yaw_quaternions([0.0, 0.0, 0.2, 0.4]),
        joint_angle_actions=np.ones((3, 42), dtype=float),
        controller_joint_angle_actions=np.ones((3, 42), dtype=float),
        adhesion_onoff=np.ones((3, 6), dtype=bool),
        controller_adhesion_onoff=np.ones((3, 6), dtype=bool),
        cpg_phases=np.zeros((4, 6), dtype=float),
        timestep_s=1.0,
    )


def _synthetic_completed_pair(tmp_path: Path) -> dict:
    artifacts = {
        "raw_rollout_arrays_npz": str(tmp_path / "raw.npz"),
        "trajectory_csv": str(tmp_path / "trajectory.csv"),
        "heading_csv": str(tmp_path / "heading.csv"),
        "instantaneous_speed_csv": str(tmp_path / "speed.csv"),
        "yaw_rate_csv": str(tmp_path / "yaw.csv"),
        "walking_bouts_csv": str(tmp_path / "walking.csv"),
        "pause_bouts_csv": str(tmp_path / "pause.csv"),
        "turn_bouts_csv": str(tmp_path / "turn.csv"),
        "g5_measurements_json": str(tmp_path / "g5.json"),
    }
    key_metrics = {
        name: {
            "baseline": 2.0,
            "candidate": 1.0,
            "absolute_delta": -1.0,
            "relative_delta": -0.5,
        }
        for name in (
            "planar_displacement_mm",
            "mean_planar_speed_mm_s",
            "heading_yaw_change_rad",
            "heading_yaw_abs_change_rad",
            "trajectory_efficiency",
            "planar_path_length_mm",
            "body_height_min_mm",
            "body_height_mean_mm",
            "body_height_range_mm",
            "joint_angle_action_abs_mean",
        )
    }
    return {
        "seed": 0,
        "status": "completed",
        "overall_pass": True,
        "key_metrics": key_metrics,
        "baseline": {"raw_observations": {"artifact_paths": artifacts}},
        "candidate": {"raw_observations": {"artifact_paths": artifacts}},
    }


def _yaw_quaternions(yaws: list[float]) -> np.ndarray:
    return np.array(
        [[np.cos(yaw / 2.0), 0.0, 0.0, np.sin(yaw / 2.0)] for yaw in yaws],
        dtype=float,
    )
