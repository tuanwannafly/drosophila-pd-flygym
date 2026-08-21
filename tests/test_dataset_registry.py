"""Temporary-directory tests for Project X dataset intake."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import pytest

from drosophila_pd.dataset_registry import (
    DATASET_BUCKETS,
    DatasetChecksum,
    DatasetIndex,
    DatasetRegistry,
    DatasetScanner,
    DatasetValidator,
    DatasetVersion,
)


def _make_source(root: Path, *, name: str = "source", json_rollout: bool = False, duplicate: bool = False) -> Path:
    source = root / name
    (source / "rollouts").mkdir(parents=True)
    (source / "metadata.json").write_text(json.dumps({"authors": ["fixture"], "license": "MIT"}), encoding="utf-8")
    if json_rollout:
        (source / "rollouts" / "trajectory.json").write_text('{"timestamps": [0.0, 0.1], "frames": [[0], [1]]}', encoding="utf-8")
    else:
        payload = "frame,time_s,x,y,z\n0,0.0,0,0,0\n1,0.1,1,0,0\n"
        (source / "rollouts" / "trajectory.csv").write_text(payload, encoding="utf-8")
        if duplicate:
            (source / "rollouts" / "thorax_trajectory.csv").write_text(payload, encoding="utf-8")
    return source


def test_models_enforce_version_and_checksum_contract() -> None:
    assert str(DatasetVersion("1.2.3")) == "1.2.3"
    with pytest.raises(ValueError):
        DatasetVersion("v1")
    with pytest.raises(ValueError):
        DatasetChecksum("x", "not-a-hash", 1)
    assert DatasetChecksum("x", "0" * 64, 1).as_dict()["byte_size"] == 1


def test_registry_initializes_layout_without_payloads(tmp_path: Path) -> None:
    registry = DatasetRegistry(tmp_path / "datasets")
    registry.initialize_layout()
    assert {path.name for path in (tmp_path / "datasets").iterdir()} == set(DATASET_BUCKETS)
    assert not list((tmp_path / "datasets").rglob("*.npz"))


def test_directory_import_health_artifacts_and_browser(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    registry = DatasetRegistry(tmp_path / "datasets")
    result = registry.import_directory(source, dataset_type="healthy", dataset_id="healthy_fixture")

    assert result.status == "READY"
    assert result.manifest.root == (tmp_path / "datasets" / "healthy" / "healthy_fixture" / "0.1.0").resolve()
    assert result.health.overall_pass is True
    assert registry.search("healthy_fixture")[0].dataset_id == "healthy_fixture"
    paths = registry.write_artifacts(result.manifest, tmp_path / "reports")
    assert {
        "manifest.json",
        "dataset_summary.json",
        "dataset_inventory.csv",
        "checksums.sha256",
        "dataset_report.md",
    } <= {path.name for path in paths.values()}
    assert {"dataset_health.json", "missing_data_report.md", "duplicate_report.md", "validation_report.md", "storage_report.md"} <= {path.name for path in paths.values()}
    assert all(path.is_file() for path in paths.values())

    rescanned = DatasetRegistry(tmp_path / "datasets").scan()
    assert len(rescanned) == 1
    assert rescanned[0].status == "READY"


def test_zip_and_rollout_imports_are_explicit_and_validated(tmp_path: Path) -> None:
    source = _make_source(tmp_path, name="zip_source")
    archive_path = tmp_path / "dataset.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for path in source.rglob("*"):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())

    registry = DatasetRegistry(tmp_path / "datasets")
    zipped = registry.import_zip(archive_path, dataset_type="candidate", dataset_id="zip_fixture")
    assert zipped.status == "READY"

    rollout_a = tmp_path / "rollout_a.csv"
    rollout_b = tmp_path / "rollout_b.csv"
    rollout_a.write_text("frame,x\n0,0\n1,1\n", encoding="utf-8")
    rollout_b.write_text("frame,x\n0,0\n1,2\n", encoding="utf-8")
    imported = registry.import_rollouts(
        (rollout_a, rollout_b),
        dataset_type="control",
        dataset_id="rollout_fixture",
        metadata={"authors": ["fixture"], "license": "MIT"},
    )
    assert imported.status == "READY"
    assert imported.health.checks["trajectory"]["trajectory_count"] == 2


def test_single_rollout_without_metadata_is_failed(tmp_path: Path) -> None:
    rollout = tmp_path / "trajectory.csv"
    rollout.write_text("frame,x\n0,0\n", encoding="utf-8")
    result = DatasetRegistry(tmp_path / "datasets").import_rollout(rollout, dataset_type="healthy", dataset_id="missing_metadata")
    assert result.status == "FAILED"
    assert result.health.checks["metadata"]["pass"] is False


def test_validator_detects_duplicates_checksum_and_payload_errors(tmp_path: Path) -> None:
    source = _make_source(tmp_path, name="duplicates", duplicate=True)
    registry = DatasetRegistry(tmp_path / "datasets")
    duplicate = registry.import_directory(source, dataset_type="healthy", dataset_id="duplicates")
    assert duplicate.status == "FAILED"
    assert duplicate.health.checks["duplicate_rollouts"]["pass"] is False

    valid_source = _make_source(tmp_path, name="mismatch")
    valid = registry.import_directory(valid_source, dataset_type="healthy", dataset_id="mismatch")
    target = valid.manifest.root / "rollouts" / "trajectory.csv"
    target.write_text(target.read_text(encoding="utf-8") + "2,0.2,2,0,0\n", encoding="utf-8")
    report = DatasetValidator().validate(valid.manifest)
    assert report.checks["checksums"]["pass"] is False

    broken = _make_source(tmp_path, name="broken", json_rollout=True)
    (broken / "rollouts" / "trajectory.json").write_text("{broken", encoding="utf-8")
    broken_result = registry.import_directory(broken, dataset_type="healthy", dataset_id="broken")
    assert broken_result.health.checks["payload_quality"]["pass"] is False
    assert broken_result.health.checks["payload_quality"]["corrupted_json"]


def test_unsafe_zip_is_rejected_and_empty_scan_waits(tmp_path: Path) -> None:
    archive_path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "no")
    with pytest.raises(ValueError):
        DatasetScanner().scan_source(archive_path)

    report = DatasetScanner().scan(tmp_path / "empty")
    assert report == ()


def test_validator_detects_manifest_parse_and_timestamp_frame_errors(tmp_path: Path) -> None:
    source = tmp_path / "quality"
    (source / "rollouts").mkdir(parents=True)
    (source / "metadata.json").write_text("{}", encoding="utf-8")
    trajectory = source / "rollouts" / "trajectory.csv"
    trajectory.write_text("frame,time_s,x\n0,0.2,0\n2,0.1,1\n", encoding="utf-8")
    (source / "manifest.json").write_text("{broken", encoding="utf-8")
    manifest = DatasetScanner().scan_source(source, dataset_type="healthy", dataset_id="quality")
    report = DatasetValidator().validate(manifest)
    assert report.overall_pass is False
    assert report.checks["manifest"]["parse_errors"] is False
    assert report.checks["payload_quality"]["invalid_timestamps"]
    assert report.checks["payload_quality"]["missing_frames"]


def test_index_filters_status_type_and_tags(tmp_path: Path) -> None:
    source = _make_source(tmp_path)
    result = DatasetRegistry(tmp_path / "datasets").import_directory(source, dataset_type="healthy", dataset_id="tagged")
    metadata = result.manifest.metadata
    assert metadata is not None
    tagged = result.manifest.__class__(**{**result.manifest.__dict__, "metadata": metadata.__class__(**{**metadata.__dict__, "tags": ("baseline",)})})
    index = DatasetIndex([tagged])
    assert index.search(dataset_type="healthy", status="READY", tags=("baseline",))[0].dataset_id == "tagged"
