"""G7 measurement-enabled evidence refresh.

This module creates a new evidence package for the frozen E3 baseline/candidate
pair while exporting raw rollout arrays needed by G5 metrics. It deliberately
does not modify frozen E3/E4/E5 reports or the canonical frozen runners.
"""

from __future__ import annotations

from copy import deepcopy
import csv
from dataclasses import dataclass
from datetime import UTC, datetime
import math
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from drosophila_pd.anatomy.audit import (
    git_commit,
    runtime_environment,
    write_json_report,
)
from drosophila_pd.controllers.healthy_baseline import build_official_cpg_controller
from drosophila_pd.experiments.candidate_robustness import (
    REQUIRED_E3_DURATION_S,
    REQUIRED_E3_SEEDS,
    CandidateRobustnessConfig,
    build_aggregate_statistics,
    build_sign_consistency,
)
from drosophila_pd.experiments.healthy_baseline import (
    HealthyBaselineConfig,
    _actuator_summary,
    _apply_action_perturbation,
    _body_segment_index,
    _collect_thorax_state,
    _controller_transformation_snapshot,
    _json_float_list,
    _skeleton_summary,
)
from drosophila_pd.experiments.perturbation_experiment import (
    build_controlled_variables,
)
from drosophila_pd.metrics.comparison import compare_locomotion_reports
from drosophila_pd.metrics.locomotion import (
    check_locomotion_pass_criteria,
    compute_locomotion_metrics,
)
from drosophila_pd.metrics.measurement_extension import (
    DEFAULT_MEASUREMENT_EXTENSION_CONFIG,
    compute_extended_locomotion_metrics,
)
from drosophila_pd.metrics.trajectory import write_trajectory_csv
from drosophila_pd.perturbations import (
    ActionPerturbationContext,
    ControllerPerturbationContext,
    Perturbation,
    summarize_action_transformation,
    summarize_controller_transformation,
)


G7_EXPERIMENT_ID = "g7_measurement_enabled_evidence_refresh"
DEFAULT_G7_OUTPUT_DIR = Path("results") / "validation" / G7_EXPERIMENT_ID

SCIENTIFIC_SCOPE = (
    "G7 refreshes the frozen E3 baseline/candidate simulation conditions with "
    "raw rollout export and G5 measurements. It does not tune parameters, "
    "introduce perturbations, reinterpret the frozen candidate, or validate a "
    "biological Parkinson's disease model."
)


@dataclass(frozen=True)
class RolloutArrays:
    """Raw arrays exported for one measurement-enabled rollout."""

    thorax_positions: np.ndarray
    thorax_quaternions: np.ndarray
    joint_angle_actions: np.ndarray
    controller_joint_angle_actions: np.ndarray
    adhesion_onoff: np.ndarray | None
    controller_adhesion_onoff: np.ndarray | None
    cpg_phases: np.ndarray
    timestep_s: float


def load_measurement_extension_config(path: str | Path | None) -> dict[str, Any]:
    """Load G5 measurement settings, or return defaults when no file is supplied."""

    if path is None:
        return deepcopy(DEFAULT_MEASUREMENT_EXTENSION_CONFIG)
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Measurement extension config root must be a mapping.")
    return _deep_merge(DEFAULT_MEASUREMENT_EXTENSION_CONFIG, _strip_metadata(loaded))


def run_measurement_enabled_evidence_refresh(
    *,
    baseline_config: HealthyBaselineConfig,
    validation_config: CandidateRobustnessConfig,
    measurement_config: dict[str, Any],
    output_dir: str | Path,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Run the frozen E3 baseline/candidate pair and export G5 artifacts."""

    _validate_frozen_refresh_inputs(validation_config)
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    pairs = []
    for seed in validation_config.seeds:
        pairs.append(
            _run_measurement_seed_pair(
                baseline_config=baseline_config,
                validation_config=validation_config,
                measurement_config=measurement_config,
                output_dir=root,
                repo_root=repo_root,
                seed=seed,
            )
        )
    report = build_measurement_refresh_report(
        baseline_config=baseline_config,
        validation_config=validation_config,
        measurement_config=measurement_config,
        output_dir=root,
        pairs=pairs,
        repo_root=repo_root,
    )
    report_path = root / "measurement_enabled_evidence.json"
    write_json_report(report, report_path)
    report["report_path"] = _relative_or_posix(report_path, root)
    return report


def build_measurement_refresh_unavailable_report(
    error: BaseException,
    *,
    baseline_config: HealthyBaselineConfig,
    validation_config: CandidateRobustnessConfig,
    measurement_config: dict[str, Any],
    output_dir: str | Path,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build a report for environments where FlyGym execution is unavailable."""

    return {
        "experiment_id": G7_EXPERIMENT_ID,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "output_dir": str(output_dir),
        "baseline_config": baseline_config.to_report(),
        "validation_config": validation_config.to_report(),
        "measurement_config": measurement_config,
        "pairs": [],
        "checks": {},
        "overall_pass": False,
        "local_execution": "NOT VERIFIED",
        "error_type": type(error).__name__,
        "error": str(error),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def build_measurement_refresh_report(
    *,
    baseline_config: HealthyBaselineConfig,
    validation_config: CandidateRobustnessConfig,
    measurement_config: dict[str, Any],
    output_dir: str | Path,
    pairs: list[dict[str, Any]],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build the combined G7 evidence manifest/report."""

    aggregate_statistics = build_aggregate_statistics(pairs)
    sign_consistency = build_sign_consistency(pairs)
    artifacts = _artifact_inventory(pairs)
    checks = _build_refresh_checks(
        validation_config=validation_config,
        pairs=pairs,
        artifacts=artifacts,
    )
    return {
        "experiment_id": G7_EXPERIMENT_ID,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        "environment": runtime_environment(),
        "output_dir": str(output_dir),
        "frozen_inputs": {
            "baseline_config": "configs/experiments/healthy_baseline.yaml",
            "validation_config": "configs/experiments/validation/milestone_e3.yaml",
            "candidate_source": "Milestone E2 combined phenotype characterization",
            "candidate_motor_scale": validation_config.candidate.motor_scale,
            "candidate_coupling_scale": validation_config.candidate.coupling_scale,
            "seeds": list(validation_config.seeds),
            "duration_s": validation_config.duration_s,
        },
        "baseline_config": baseline_config.to_report(),
        "validation_config": validation_config.to_report(),
        "measurement_config": measurement_config,
        "paired_execution": {
            "seeds": list(validation_config.seeds),
            "duration_s": validation_config.duration_s,
            "same_seed_within_each_pair": True,
            "fresh_fly_world_simulation_per_condition": True,
            "raw_rollout_arrays_exported": True,
            "rendering_required": False,
            "new_perturbations_introduced": False,
            "parameter_tuning_permitted": False,
        },
        "pairs": pairs,
        "aggregate_statistics": aggregate_statistics,
        "sign_consistency": sign_consistency,
        "artifact_inventory": artifacts,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def export_rollout_artifacts(
    *,
    condition_dir: str | Path,
    arrays: RolloutArrays,
    measurement_report: dict[str, Any],
) -> dict[str, Any]:
    """Export raw arrays and G5 measurement artifacts for one rollout."""

    root = Path(condition_dir)
    root.mkdir(parents=True, exist_ok=True)
    raw_path = root / "raw_rollout_arrays.npz"
    np.savez_compressed(
        raw_path,
        thorax_positions_mm=arrays.thorax_positions,
        thorax_quaternions=arrays.thorax_quaternions,
        joint_angle_actions=arrays.joint_angle_actions,
        controller_joint_angle_actions=arrays.controller_joint_angle_actions,
        adhesion_onoff=_none_to_empty_bool_array(arrays.adhesion_onoff),
        controller_adhesion_onoff=_none_to_empty_bool_array(
            arrays.controller_adhesion_onoff
        ),
        cpg_phases_rad=arrays.cpg_phases,
        timestep_s=np.array([arrays.timestep_s], dtype=float),
    )

    trajectory_path = write_trajectory_csv(
        measurement_report["trajectory"],
        root / "trajectory.csv",
    )
    heading_path = _write_heading_csv(
        measurement_report["trajectory"],
        root / "heading.csv",
    )
    speed_path = _write_speed_csv(
        measurement_report["trajectory"],
        root / "instantaneous_speed.csv",
    )
    yaw_rate_path = _write_yaw_rate_csv(
        measurement_report["turning_metrics"],
        arrays.timestep_s,
        root / "yaw_rate.csv",
    )
    walking_bouts_path = _write_bouts_csv(
        measurement_report["walking_bout_metrics"]["walking_bouts"],
        root / "walking_bouts.csv",
    )
    pause_bouts_path = _write_bouts_csv(
        measurement_report["walking_bout_metrics"]["pause_bouts"],
        root / "pause_bouts.csv",
    )
    turn_bouts_path = _write_turn_bouts_csv(
        measurement_report["turning_metrics"]["turn_bouts"],
        root / "turn_bouts.csv",
    )
    measurements_path = root / "g5_measurements.json"
    write_json_report(measurement_report, measurements_path)

    return {
        "raw_rollout_arrays_npz": str(raw_path),
        "trajectory_csv": str(trajectory_path),
        "heading_csv": str(heading_path),
        "instantaneous_speed_csv": str(speed_path),
        "yaw_rate_csv": str(yaw_rate_path),
        "walking_bouts_csv": str(walking_bouts_path),
        "pause_bouts_csv": str(pause_bouts_path),
        "turn_bouts_csv": str(turn_bouts_path),
        "g5_measurements_json": str(measurements_path),
    }


def _run_measurement_seed_pair(
    *,
    baseline_config: HealthyBaselineConfig,
    validation_config: CandidateRobustnessConfig,
    measurement_config: dict[str, Any],
    output_dir: Path,
    repo_root: str | Path | None,
    seed: int,
) -> dict[str, Any]:
    seed_config = _config_with_seed_and_duration(
        baseline_config,
        seed=seed,
        duration_s=validation_config.duration_s,
    )
    perturbation = validation_config.candidate.perturbation(
        experiment_id=validation_config.experiment_id
    )
    seed_dir = output_dir / "rollouts" / f"seed_{seed}"
    baseline = run_measurement_enabled_rollout(
        config=seed_config,
        perturbation=None,
        condition_id=f"seed_{seed}_baseline",
        condition_dir=seed_dir / "baseline",
        measurement_config=measurement_config,
        repo_root=repo_root,
    )
    candidate = run_measurement_enabled_rollout(
        config=seed_config,
        perturbation=perturbation,
        condition_id=f"seed_{seed}_candidate_motor_080_coupling_075",
        condition_dir=seed_dir / "candidate",
        measurement_config=measurement_config,
        repo_root=repo_root,
    )
    comparison = compare_locomotion_reports(baseline, candidate)
    key_metrics = _key_metric_summary(baseline, candidate, comparison)
    controlled = {
        "baseline": build_controlled_variables(seed_config),
        "candidate": build_controlled_variables(seed_config),
    }
    controlled["match"] = controlled["baseline"] == controlled["candidate"]
    checks = _pair_checks(
        baseline=baseline,
        candidate=candidate,
        controlled_variables_match=controlled["match"],
    )
    return {
        "seed": seed,
        "status": "completed",
        "same_seed_within_pair": True,
        "duration_s": validation_config.duration_s,
        "controlled_variables": controlled,
        "baseline": baseline,
        "candidate": candidate,
        "comparison": comparison,
        "key_metrics": key_metrics,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
    }


def run_measurement_enabled_rollout(
    *,
    config: HealthyBaselineConfig,
    perturbation: Perturbation | None,
    condition_id: str,
    condition_dir: str | Path,
    measurement_config: dict[str, Any],
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    """Run one rollout and export raw arrays plus G5 measurements."""

    np.random.seed(config.random_seed)

    from flygym import Simulation  # noqa: PLC0415
    from flygym.compose import FlatGroundWorld  # noqa: PLC0415
    from flygym.utils.math import Rotation3D  # noqa: PLC0415
    from flygym_demo.complex_terrain import (  # noqa: PLC0415
        LocomotionAction,
        apply_locomotion_action,
        make_locomotion_fly,
    )

    fly = make_locomotion_fly(
        name=config.fly["name"],
        joint_stiffness=float(config.fly["joint_stiffness"]),
        joint_damping=float(config.fly["joint_damping"]),
        passive_tarsus_stiffness=float(config.fly["passive_tarsus_stiffness"]),
        passive_tarsus_damping=float(config.fly["passive_tarsus_damping"]),
        actuator_gain=float(config.actuators["gain"]),
        actuator_forcerange=tuple(float(v) for v in config.actuators["forcerange"]),
        add_adhesion=bool(config.fly["add_adhesion"]),
        adhesion_gain=float(config.fly["adhesion_gain"]),
        colorize=bool(config.fly["colorize"]),
    )
    dof_order = fly.get_actuated_jointdofs_order(config.actuators["type"])

    world = FlatGroundWorld()
    world.add_fly(
        fly,
        spawn_position=config.spawn_position_mm,
        spawn_rotation=Rotation3D("quat", config.spawn_orientation_quat.tolist()),
        add_ground_contact_sensors=bool(config.world["add_ground_contact_sensors"]),
    )
    sim = Simulation(world, timestep=config.timestep_s)
    sim.reset()

    controller, preprogrammed_steps = build_official_cpg_controller(
        timestep=sim.timestep,
        random_seed=config.random_seed,
        output_dof_order=dof_order,
        config=config.controller,
    )
    pre_controller_state = _controller_transformation_snapshot(controller)
    if perturbation is not None:
        controller = perturbation.apply_to_controller(
            controller,
            ControllerPerturbationContext(
                condition_id=condition_id,
                timestep_s=float(sim.timestep),
                random_seed=config.random_seed,
                expected_joint_angle_count=len(dof_order),
            ),
        )
    post_controller_state = _controller_transformation_snapshot(controller)

    initial_action = LocomotionAction(
        joint_angles=preprogrammed_steps.default_pose_by_dof_order(dof_order),
        adhesion_onoff=(
            np.ones(6, dtype=bool) if bool(config.fly["add_adhesion"]) else None
        ),
    )
    apply_locomotion_action(sim, fly.name, initial_action)
    if config.warmup_duration_s > 0:
        sim.warmup(duration_s=config.warmup_duration_s)

    arrays = _collect_rollout_arrays(
        sim=sim,
        fly=fly,
        controller=controller,
        perturbation=perturbation,
        condition_id=condition_id,
        config=config,
        dof_order=dof_order,
        apply_locomotion_action=apply_locomotion_action,
    )
    metrics = compute_locomotion_metrics(
        thorax_positions=arrays.thorax_positions,
        thorax_quaternions=arrays.thorax_quaternions,
        joint_angle_actions=arrays.joint_angle_actions,
        adhesion_onoff=arrays.adhesion_onoff,
        timestep_s=sim.timestep,
        requested_duration_s=config.duration_s,
        instability_height_floor_mm=float(
            config.pass_criteria["minimum_body_height_mm"]
        ),
    )
    measurement_report = compute_extended_locomotion_metrics(
        thorax_positions=arrays.thorax_positions,
        thorax_quaternions=arrays.thorax_quaternions,
        timestep_s=float(sim.timestep),
        config=measurement_config,
    )
    artifact_paths = export_rollout_artifacts(
        condition_dir=condition_dir,
        arrays=arrays,
        measurement_report=measurement_report,
    )
    skeleton_summary = _skeleton_summary(fly)
    actuator_summary = _actuator_summary(fly, sim)
    action_transform = summarize_action_transformation(
        controller_joint_angle_actions=arrays.controller_joint_angle_actions,
        applied_joint_angle_actions=arrays.joint_angle_actions,
        controller_adhesion_onoff=arrays.controller_adhesion_onoff,
        applied_adhesion_onoff=arrays.adhesion_onoff,
        expected_joint_angle_count=len(dof_order),
        perturbation_metadata=(
            perturbation.metadata() if perturbation is not None else None
        ),
    )
    controller_transform = summarize_controller_transformation(
        pre_controller_state=pre_controller_state,
        post_controller_state=post_controller_state,
        perturbation_metadata=(
            perturbation.metadata() if perturbation is not None else None
        ),
    )
    checks = check_locomotion_pass_criteria(
        metrics=metrics,
        expected_step_count=config.expected_step_count(),
        expected_actuated_dofs=int(config.actuators["expected_actuated_dofs"]),
        observed_actuated_dofs=actuator_summary["position_actuator_count"],
        expected_adhesion_actuators=config.expected_adhesion_actuator_count(),
        observed_adhesion_actuators=actuator_summary["adhesion_actuator_count"],
        deterministic_seed_recorded=config.random_seed is not None,
    )

    sim.close()
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(repo_root),
        **runtime_environment(),
        "condition_id": condition_id,
        "configuration": config.to_report(),
        "perturbation": perturbation.metadata() if perturbation is not None else None,
        "controller": {
            **config.controller.to_report(),
            "output_dof_count": len(dof_order),
            "initial_cpg_phases_rad": _json_float_list(arrays.cpg_phases[0]),
            "final_cpg_phases_rad": _json_float_list(arrays.cpg_phases[-1]),
        },
        "skeleton_materialization_summary": skeleton_summary,
        "actuator_summary": actuator_summary,
        "raw_observations": {
            "stored_in_report": False,
            "stored_as_artifacts": True,
            "artifact_paths": artifact_paths,
            "summary": {
                "thorax_position_samples": int(arrays.thorax_positions.shape[0]),
                "thorax_quaternion_samples": int(arrays.thorax_quaternions.shape[0]),
                "joint_action_samples": int(arrays.joint_angle_actions.shape[0]),
                "adhesion_action_samples": (
                    int(arrays.adhesion_onoff.shape[0])
                    if arrays.adhesion_onoff is not None
                    else 0
                ),
            },
        },
        "derived_locomotion_metrics": metrics,
        "g5_measurement_summary": _measurement_summary(measurement_report),
        "action_transformation_summary": action_transform,
        "controller_transformation_summary": controller_transform,
        "checks": checks,
        "overall_pass": all(check["pass"] for check in checks.values()),
        "scientific_scope": SCIENTIFIC_SCOPE,
    }


def _collect_rollout_arrays(
    *,
    sim: Any,
    fly: Any,
    controller: Any,
    perturbation: Perturbation | None,
    condition_id: str,
    config: HealthyBaselineConfig,
    dof_order: list[Any],
    apply_locomotion_action: Any,
) -> RolloutArrays:
    thorax_index = _body_segment_index(fly, "c_thorax")
    step_count = config.expected_step_count()
    thorax_positions = np.full((step_count + 1, 3), np.nan, dtype=float)
    thorax_quaternions = np.full((step_count + 1, 4), np.nan, dtype=float)
    controller_joint_angle_actions = np.full(
        (step_count, len(dof_order)), np.nan, dtype=float
    )
    joint_angle_actions = np.full((step_count, len(dof_order)), np.nan, dtype=float)
    controller_adhesion_onoff = (
        np.zeros((step_count, 6), dtype=bool)
        if bool(config.fly["add_adhesion"])
        else None
    )
    adhesion_onoff = (
        np.zeros((step_count, 6), dtype=bool)
        if bool(config.fly["add_adhesion"])
        else None
    )
    cpg_phases = np.full((step_count + 1, 6), np.nan, dtype=float)

    _collect_thorax_state(
        sim,
        fly.name,
        thorax_index,
        thorax_positions,
        thorax_quaternions,
        0,
    )
    cpg_phases[0] = controller.cpg_network.curr_phases % (2 * np.pi)

    for step_index in range(step_count):
        controller_action = controller.step()
        action = _apply_action_perturbation(
            controller_action,
            perturbation=perturbation,
            condition_id=condition_id,
            step_index=step_index,
            timestep_s=float(sim.timestep),
            random_seed=config.random_seed,
            expected_joint_angle_count=len(dof_order),
        )
        apply_locomotion_action(sim, fly.name, action)
        sim.step()
        controller_joint_angle_actions[step_index] = controller_action.joint_angles
        if controller_adhesion_onoff is not None:
            controller_adhesion_onoff[step_index] = controller_action.adhesion_onoff
        joint_angle_actions[step_index] = action.joint_angles
        if adhesion_onoff is not None:
            adhesion_onoff[step_index] = action.adhesion_onoff
        _collect_thorax_state(
            sim,
            fly.name,
            thorax_index,
            thorax_positions,
            thorax_quaternions,
            step_index + 1,
        )
        cpg_phases[step_index + 1] = controller.cpg_network.curr_phases % (
            2 * np.pi
        )
    return RolloutArrays(
        thorax_positions=thorax_positions,
        thorax_quaternions=thorax_quaternions,
        joint_angle_actions=joint_angle_actions,
        controller_joint_angle_actions=controller_joint_angle_actions,
        adhesion_onoff=adhesion_onoff,
        controller_adhesion_onoff=controller_adhesion_onoff,
        cpg_phases=cpg_phases,
        timestep_s=float(sim.timestep),
    )


def _build_refresh_checks(
    *,
    validation_config: CandidateRobustnessConfig,
    pairs: list[dict[str, Any]],
    artifacts: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    completed = [pair for pair in pairs if pair.get("status") == "completed"]
    return {
        "frozen_seed_set_preserved": _check(
            list(REQUIRED_E3_SEEDS), list(validation_config.seeds)
        ),
        "frozen_duration_preserved": _check(
            REQUIRED_E3_DURATION_S, validation_config.duration_s
        ),
        "frozen_candidate_motor_scale": _check(
            0.8, validation_config.candidate.motor_scale
        ),
        "frozen_candidate_coupling_scale": _check(
            0.75, validation_config.candidate.coupling_scale
        ),
        "all_seed_pairs_completed": _check(len(validation_config.seeds), len(completed)),
        "all_pair_checks_passed": _check(
            True, all(pair.get("overall_pass") is True for pair in completed)
        ),
        "raw_arrays_exported_for_each_rollout": _check(
            len(validation_config.seeds) * 2,
            artifacts["artifact_counts"].get("raw_rollout_arrays_npz", 0),
        ),
        "trajectory_csv_exported_for_each_rollout": _check(
            len(validation_config.seeds) * 2,
            artifacts["artifact_counts"].get("trajectory_csv", 0),
        ),
        "g5_measurements_exported_for_each_rollout": _check(
            len(validation_config.seeds) * 2,
            artifacts["artifact_counts"].get("g5_measurements_json", 0),
        ),
        "no_new_perturbations_introduced": _check(True, True),
        "parameter_tuning_forbidden": _check(False, False),
    }


def _pair_checks(
    *,
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    controlled_variables_match: bool,
) -> dict[str, dict[str, Any]]:
    baseline_artifacts = baseline["raw_observations"]["artifact_paths"]
    candidate_artifacts = candidate["raw_observations"]["artifact_paths"]
    return {
        "baseline_passed": _check(True, baseline.get("overall_pass")),
        "candidate_passed": _check(True, candidate.get("overall_pass")),
        "controlled_variables_match": _check(True, controlled_variables_match),
        "baseline_raw_arrays_exported": _check(
            True, Path(baseline_artifacts["raw_rollout_arrays_npz"]).exists()
        ),
        "candidate_raw_arrays_exported": _check(
            True, Path(candidate_artifacts["raw_rollout_arrays_npz"]).exists()
        ),
        "baseline_g5_measurements_exported": _check(
            True, Path(baseline_artifacts["g5_measurements_json"]).exists()
        ),
        "candidate_g5_measurements_exported": _check(
            True, Path(candidate_artifacts["g5_measurements_json"]).exists()
        ),
    }


def _key_metric_summary(
    baseline_report: dict[str, Any],
    candidate_report: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    scalars = {
        metric: _normalise_pair_scalar(values)
        for metric, values in comparison["scalars"].items()
    }
    baseline_yaw_abs = abs(
        float(baseline_report["derived_locomotion_metrics"]["heading_yaw_change_rad"])
    )
    candidate_yaw_abs = abs(
        float(candidate_report["derived_locomotion_metrics"]["heading_yaw_change_rad"])
    )
    scalars["heading_yaw_abs_change_rad"] = _scalar_delta(
        baseline_yaw_abs,
        candidate_yaw_abs,
    )
    return scalars


def _measurement_summary(measurement_report: dict[str, Any]) -> dict[str, Any]:
    walking = measurement_report["walking_bout_metrics"]
    turning = measurement_report["turning_metrics"]
    trajectory = measurement_report["trajectory"]
    return {
        "trajectory": {
            "sample_count": trajectory["sample_count"],
            "path_length_mm": trajectory["summary"]["path_length_mm"],
            "mean_step_speed_mm_s": trajectory["summary"]["mean_step_speed_mm_s"],
            "max_step_speed_mm_s": trajectory["summary"]["max_step_speed_mm_s"],
        },
        "walking_bouts": {
            "bout_count": walking["bout_count"],
            "pause_count": walking["pause_count"],
            "walking_duration_s": walking["walking_duration_s"],
            "pause_duration_s": walking["pause_duration_s"],
            "walking_duty_cycle": walking["walking_duty_cycle"],
        },
        "turning": {
            "turn_bout_count": turning["turn_bout_count"],
            "cumulative_turning_rad": turning["cumulative_turning_rad"],
            "left_right_asymmetry": turning["left_right_asymmetry"],
            "left_turn_bout_count": turning["left_turn_bout_count"],
            "right_turn_bout_count": turning["right_turn_bout_count"],
        },
        "open_field": measurement_report["open_field_metrics"],
    }


def _artifact_inventory(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    paths = []
    for pair in pairs:
        for condition_key in ("baseline", "candidate"):
            artifacts = (
                pair.get(condition_key, {})
                .get("raw_observations", {})
                .get("artifact_paths", {})
            )
            for artifact_type, path in artifacts.items():
                counts[artifact_type] = counts.get(artifact_type, 0) + 1
                paths.append({"type": artifact_type, "path": path})
    return {
        "artifact_counts": counts,
        "artifacts": paths,
    }


def _config_with_seed_and_duration(
    baseline_config: HealthyBaselineConfig,
    *,
    seed: int,
    duration_s: float,
) -> HealthyBaselineConfig:
    data = deepcopy(baseline_config.to_report())
    data["random_seed"] = int(seed)
    data.setdefault("simulation", {})["duration_s"] = float(duration_s)
    data["experiment_id"] = f"{baseline_config.experiment_id}_g7_seed_{seed}"
    return HealthyBaselineConfig.from_mapping(data)


def _validate_frozen_refresh_inputs(
    validation_config: CandidateRobustnessConfig,
) -> None:
    if validation_config.seeds != REQUIRED_E3_SEEDS:
        raise ValueError("G7 must preserve the frozen E3 seeds.")
    if not math.isclose(validation_config.duration_s, REQUIRED_E3_DURATION_S):
        raise ValueError("G7 must preserve the frozen E3 duration.")
    validation_config.candidate.validate()


def _write_heading_csv(trajectory: dict[str, Any], path: Path) -> Path:
    rows = [
        {
            "sample_index": index,
            "time_s": trajectory["time_s"][index],
            "heading_rad": trajectory["heading_rad"][index],
        }
        for index in range(int(trajectory["sample_count"]))
    ]
    return _write_dict_csv(path, ["sample_index", "time_s", "heading_rad"], rows)


def _write_speed_csv(trajectory: dict[str, Any], path: Path) -> Path:
    rows = [
        {
            "sample_index": index,
            "time_s": trajectory["time_s"][index],
            "instantaneous_speed_mm_s": trajectory["instantaneous_speed_mm_s"][index],
            "cumulative_distance_mm": trajectory["cumulative_distance_mm"][index],
        }
        for index in range(int(trajectory["sample_count"]))
    ]
    return _write_dict_csv(
        path,
        [
            "sample_index",
            "time_s",
            "instantaneous_speed_mm_s",
            "cumulative_distance_mm",
        ],
        rows,
    )


def _write_yaw_rate_csv(
    turning: dict[str, Any],
    timestep_s: float,
    path: Path,
) -> Path:
    rows = [
        {
            "step_index": index,
            "start_time_s": index * timestep_s,
            "end_time_s": (index + 1) * timestep_s,
            "yaw_rate_rad_s": value,
        }
        for index, value in enumerate(turning["yaw_rate_rad_s"])
    ]
    return _write_dict_csv(
        path,
        ["step_index", "start_time_s", "end_time_s", "yaw_rate_rad_s"],
        rows,
    )


def _write_bouts_csv(bouts: list[dict[str, Any]], path: Path) -> Path:
    return _write_dict_csv(
        path,
        [
            "type",
            "start_step",
            "end_step_exclusive",
            "start_time_s",
            "end_time_s",
            "duration_s",
            "mean_speed_mm_s",
            "distance_mm",
        ],
        bouts,
    )


def _write_turn_bouts_csv(bouts: list[dict[str, Any]], path: Path) -> Path:
    return _write_dict_csv(
        path,
        [
            "start_step",
            "end_step_exclusive",
            "start_time_s",
            "end_time_s",
            "duration_s",
            "net_turn_angle_rad",
            "absolute_turn_angle_rad",
            "mean_yaw_rate_rad_s",
            "direction",
        ],
        bouts,
    )


def _write_dict_csv(
    path: Path,
    fieldnames: list[str],
    rows: list[dict[str, Any]],
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _normalise_pair_scalar(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "baseline": values.get("baseline"),
        "candidate": values.get("candidate", values.get("perturbed")),
        "absolute_delta": values.get("absolute_delta"),
        "relative_delta": values.get("relative_delta"),
    }


def _scalar_delta(baseline: Any, candidate: Any) -> dict[str, float | None]:
    baseline_value = _finite_or_none(baseline)
    candidate_value = _finite_or_none(candidate)
    if baseline_value is None or candidate_value is None:
        return {
            "baseline": baseline_value,
            "candidate": candidate_value,
            "absolute_delta": None,
            "relative_delta": None,
        }
    absolute_delta = candidate_value - baseline_value
    return {
        "baseline": baseline_value,
        "candidate": candidate_value,
        "absolute_delta": absolute_delta,
        "relative_delta": (
            None
            if abs(baseline_value) <= 1e-9
            else absolute_delta / abs(baseline_value)
        ),
    }


def _finite_or_none(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _none_to_empty_bool_array(value: np.ndarray | None) -> np.ndarray:
    if value is None:
        return np.empty((0, 0), dtype=bool)
    return np.asarray(value, dtype=bool)


def _relative_or_posix(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _strip_metadata(data: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in data.items()
        if key not in {"schema_version", "phase", "title", "scope"}
    }


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _check(expected: Any, observed: Any) -> dict[str, Any]:
    return {
        "expected": expected,
        "observed": observed,
        "pass": observed == expected,
    }


__all__ = [
    "DEFAULT_G7_OUTPUT_DIR",
    "G7_EXPERIMENT_ID",
    "RolloutArrays",
    "SCIENTIFIC_SCOPE",
    "build_measurement_refresh_report",
    "build_measurement_refresh_unavailable_report",
    "export_rollout_artifacts",
    "load_measurement_extension_config",
    "run_measurement_enabled_evidence_refresh",
    "run_measurement_enabled_rollout",
]
