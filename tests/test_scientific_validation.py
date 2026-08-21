"""Contract tests for Epic 17 post-processing validation."""

from __future__ import annotations

import json

import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.scientific_validation import (
    ReferenceDataset,
    ReferenceDatasetManager,
    benchmark_operations,
    compare_series,
    generate_validation_report,
    hash_payload,
    repeated_execution_check,
)
from drosophila_pd.scientific_validation.statistics import effect_size_consistency


def _rollout(condition: str, offset: float = 0.0) -> RolloutData:
    count = 6
    return RolloutData(
        condition_id=condition,
        timestep_s=0.1,
        thorax_positions=np.column_stack(
            [np.arange(count, dtype=float) + offset, np.arange(count, dtype=float) * 0.1, np.ones(count)]
        ),
        thorax_quaternions=np.tile([1.0, 0.0, 0.0, 0.0], (count, 1)),
        com_positions=np.column_stack(
            [np.arange(count, dtype=float) + offset, np.zeros(count), np.ones(count)]
        ),
        joint_positions={"left_leg": np.arange(count, dtype=float), "right_leg": np.arange(count, dtype=float)},
    )


def test_compare_series_reports_requested_error_metrics():
    result = compare_series([1.0, 2.0, 3.0], [1.0, 1.0, 2.0])

    assert result["available"]
    assert result["rmse"] > 0
    assert result["mae"] > 0
    assert "r2" in result
    assert "correlation" in result


def test_reference_manager_validates_registered_in_memory_data():
    manager = ReferenceDatasetManager()
    manager.register(ReferenceDataset("test_reference", "Validation Set", {"one": _rollout("reference")}))

    result = manager.validate()
    manifest = manager.manifest()

    assert result["overall_pass"]
    assert manifest["datasets"][0]["entries"][0]["in_memory"]


def test_reference_manager_reads_manifest_and_json(tmp_path):
    reference_path = tmp_path / "reference.json"
    reference_path.write_text(
        json.dumps(
            {
                "condition_id": "reference",
                "timestep_s": 0.1,
                "thorax_positions": _rollout("reference").positions_array().tolist(),
                "thorax_quaternions": _rollout("reference").quaternions_array().tolist(),
            }
        ),
        encoding="utf-8",
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps({"datasets": [{"dataset_id": "validation", "role": "Validation Set", "rollouts": [{"entry_id": "reference", "path": "reference.json"}]}]}),
        encoding="utf-8",
    )
    manager = ReferenceDatasetManager.from_manifest(manifest_path)

    loaded = manager.get("validation").load(base_dir=tmp_path)
    assert loaded["reference"].condition_id == "reference"


def test_reproducibility_and_benchmark_are_deterministic():
    payload = {"value": np.asarray([1.0, 2.0]).tolist()}
    reproducibility = repeated_execution_check(lambda: payload, repeats=3)
    benchmark = benchmark_operations({"hash": lambda: hash_payload(payload)}, repeats=1)

    assert reproducibility["deterministic"]
    assert benchmark["operations"]["hash"]["output_hash"]
    assert hash_payload(payload) == hash_payload(payload)


def test_validation_report_writes_reports_and_figures(tmp_path):
    report = generate_validation_report(_rollout("observed"), _rollout("reference"), output_dir=tmp_path)

    assert report["overall_pass"]
    assert (tmp_path / "validation_report.json").is_file()
    assert (tmp_path / "validation_summary.csv").is_file()
    assert (tmp_path / "benchmark_report.json").is_file()
    assert (tmp_path / "reproducibility_report.json").is_file()
    assert (tmp_path / "figure_manifest.json").is_file()
    assert list((tmp_path / "figures").glob("*.png"))


def test_effect_size_requires_real_finite_groups():
    result = effect_size_consistency([1.0, 2.0, 3.0], [2.0, 3.0, 4.0])

    assert result["available"]
    assert result["cohens_d"] < 0
