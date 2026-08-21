"""Contract tests for Epic 16 computational post-processing."""

from __future__ import annotations

import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.parkinson import (
    ComputationalPDIndex,
    ParkinsonMotorConfig,
    compare_computational_reports,
    generate_computational_pd_report,
)
from drosophila_pd.parkinson.validation import (
    bootstrap_confidence_interval,
    compare_feature_sets,
    feature_ablation,
    validate_computational_report,
)


def _rollout(condition: str, scale: float = 1.0) -> RolloutData:
    count = 10
    return RolloutData(
        condition_id=condition,
        timestep_s=0.1,
        thorax_positions=np.column_stack(
            [np.arange(count, dtype=float) * scale, np.zeros(count), np.ones(count)]
        ),
        thorax_quaternions=np.tile([1.0, 0.0, 0.0, 0.0], (count, 1)),
        joint_positions={
            "left_leg": np.linspace(0.0, 0.9, count),
            "right_leg": np.linspace(0.0, 0.7, count),
        },
        metadata={"source": "deterministic software fixture"},
    )


def test_motor_model_extracts_features_and_behavior_states():
    report = generate_computational_pd_report(_rollout("candidate"), write_figures=False)

    assert report["motor_features"]["available"]["walking_velocity_mm_s"]
    assert report["behavior_model"]["available"]
    assert report["validation"]["report_checks"]["overall_pass"]
    assert report["scientific_scope"].startswith("Computational")


def test_index_reference_bootstrap_and_ablation_are_deterministic():
    index = ComputationalPDIndex(
        weights={"walking_velocity_mm_s": 2.0, "body_oscillation_mm": 1.0},
        directions={"walking_velocity_mm_s": "lower_is_impairment", "body_oscillation_mm": "higher_is_impairment"},
        bootstrap_replicates=8,
        bootstrap_seed=11,
    )
    features = {"walking_velocity_mm_s": 2.0, "body_oscillation_mm": 1.5}
    reference = {"walking_velocity_mm_s": 3.0, "body_oscillation_mm": 1.0}
    samples = {"walking_velocity_mm_s": [1.0, 2.0, 3.0]}
    result = index.evaluate(features, reference, sample_values=samples)

    assert result["available"]
    assert result["uncertainty"]["replicates"] == 8
    assert set(result["sensitivity_analysis"]["by_feature"]) == set(index.weights)
    assert result == index.evaluate(features, reference, sample_values=samples)


def test_validation_helpers_do_not_change_inputs():
    observed = {"a": 2.0, "b": None}
    reference = {"a": 1.0, "b": 3.0}
    delta = compare_feature_sets(observed, reference)
    interval = bootstrap_confidence_interval([1.0, 2.0, 3.0], replicates=16, seed=4)
    index = ComputationalPDIndex(weights={"a": 1.0})
    ablated = feature_ablation(index, observed, reference)

    assert delta["features"]["a"]["delta"] == 1.0
    assert interval["available"]
    assert ablated["by_feature"]["a"]["index_without_feature"] is None
    assert observed == {"a": 2.0, "b": None}


def test_report_package_writes_machine_and_human_outputs(tmp_path):
    report = generate_computational_pd_report(_rollout("healthy"), output_dir=tmp_path)

    assert (tmp_path / "computational_pd_report.json").is_file()
    assert (tmp_path / "motor_features.csv").is_file()
    assert (tmp_path / "computational_pd_report.md").is_file()
    assert (tmp_path / "computational_pd_report.html").is_file()
    assert report["validation"]["report_checks"]["overall_pass"]
    assert list((tmp_path / "figures").glob("*.png"))


def test_comparison_keeps_computational_condition_labels():
    healthy = generate_computational_pd_report(_rollout("Healthy"), write_figures=False)
    candidate = generate_computational_pd_report(_rollout("Candidate", 0.8), write_figures=False)
    comparison = compare_computational_reports({"Healthy": healthy, "Candidate": candidate}, reference_name="Healthy")

    assert comparison["conditions"] == ["Healthy", "Candidate"]
    assert comparison["reference"] == "Healthy"
    assert comparison["scope"].startswith("Computational")
    assert comparison["feature_distance_matrix"]["values"][0][0] == 0.0


def test_scope_validator_rejects_positive_biological_upgrade():
    report = {
        "scientific_scope": "Computational report with biological validation confirmed.",
        "motor_features": {},
        "behavior_model": {},
    }
    assert not validate_computational_report(report)["overall_pass"]
