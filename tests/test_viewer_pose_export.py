from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from drosophila_pd.viewer_export import (
    VIEWER_POSE_SCHEMA,
    PoseValidationError,
    export_viewer_pose,
    load_rollout_inputs,
    validate_pose_document,
)


def test_pose_export_converts_adapter_rollout_to_viewer_schema(tmp_path: Path) -> None:
    dataset = _write_fixture(tmp_path)
    output = tmp_path / "viewer_pose.json"

    result = export_viewer_pose(dataset, output)
    document = json.loads(output.read_text(encoding="utf-8"))

    assert result.validation.overall_pass is True
    assert document["frame_count"] == 3
    assert document["joint_names"] == ["joint_a"]
    assert document["metadata"]["quaternion_order"] == "xyzw"
    assert document["metadata"]["body_segment_names"] == ["thorax", "head"]
    assert document["mesh"]["render_mode"] == "procedural_fallback"
    assert document["mesh"]["scientific_mesh"] is False
    assert document["mesh"]["asset"] is None
    assert document["mesh"]["body_segment_names"] == ["thorax", "head"]
    assert document["mesh"]["mesh_instances"]
    assert document["frames"][0]["orientation"] == [0.0, 0.0, 0.0, 1.0]
    assert document["frames"][0]["skeleton"]["source"] == "rollout.body_positions"
    assert document["frames"][0]["skeleton"]["bones"][0]["id"] == "thorax"
    assert document["frames"][1]["trajectory"]["thorax"] == [1.0, 0.0, 1.0]
    assert document["frames"][0]["joint_velocity"]["joint_a"] == 2.0
    assert document["frames"][0]["visibility"]["COM"] is True
    assert all(path.is_file() for path in result.source_files)


def test_pose_export_accepts_adapter_rollout_npz_name(tmp_path: Path) -> None:
    dataset = _write_fixture(tmp_path, npz_name="rollout.npz")
    output = tmp_path / "viewer_pose.json"

    result = export_viewer_pose(dataset, output)

    assert result.validation.overall_pass is True
    assert result.source_files[1].name == "rollout.npz"
    assert validate_pose_document(result.document).overall_pass is True


def test_pose_export_resolves_dataset_id_from_search_root(tmp_path: Path) -> None:
    dataset = _write_fixture(tmp_path / "datasets" / "healthy")
    output = tmp_path / "viewer_pose.json"

    result = export_viewer_pose("Healthy_001", output, search_roots=[tmp_path / "datasets"])

    assert result.validation.overall_pass is True
    assert result.source_files[0].parent == dataset.resolve()


def test_pose_export_passes_json_schema_validation(tmp_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    dataset = _write_fixture(tmp_path)
    output = tmp_path / "viewer_pose.json"
    export_viewer_pose(dataset, output)
    document = json.loads(output.read_text(encoding="utf-8"))

    jsonschema.Draft202012Validator(VIEWER_POSE_SCHEMA).validate(document)
    assert validate_pose_document(document).overall_pass is True


def test_validator_rejects_nan_and_non_normalized_quaternion() -> None:
    document = _pose_document()
    document["frames"][0]["thorax"][0] = float("nan")
    document["frames"][1]["orientation"] = [0.0, 0.0, 0.0, 2.0]

    report = validate_pose_document(document, raise_on_error=False)

    assert report.overall_pass is False
    assert report.checks["no_nan"]["pass"] is False
    assert report.checks["quaternion_normalized"]["pass"] is False
    with pytest.raises(PoseValidationError):
        validate_pose_document(document)


def test_loader_rejects_mismatched_input_frame_counts(tmp_path: Path) -> None:
    dataset = _write_fixture(tmp_path)
    arrays_path = dataset / "rollout_arrays.npz"
    arrays = dict(np.load(arrays_path))
    np.savez_compressed(
        arrays_path,
        thorax_positions=arrays["thorax_positions"],
        thorax_quaternions=arrays["thorax_quaternions"][:2],
        time_s=arrays["time_s"],
    )

    with pytest.raises(ValueError, match="frame counts"):
        load_rollout_inputs(dataset)


def test_pose_export_reconstructs_duplicated_timestamps_from_metadata(tmp_path: Path) -> None:
    dataset = _write_fixture(tmp_path, time_s=np.asarray([0.0, 0.0, 0.0], dtype=float))
    output = tmp_path / "viewer_pose.json"

    result = export_viewer_pose(dataset, output)
    times = [frame["time"] for frame in result.document["frames"]]

    assert result.validation.overall_pass is True
    assert times == [0.0, 0.5, 1.0]
    assert result.document["metadata"]["timestamps_reconstructed"] is True


def test_pose_export_normalizes_and_repairs_wxyz_quaternions(tmp_path: Path) -> None:
    dataset = _write_fixture(
        tmp_path,
        quaternions=np.asarray(
            [
                [2.0, 0.0, 0.0, 0.0],
                [0.0, 0.0, 0.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ],
            dtype=float,
        ),
    )
    output = tmp_path / "viewer_pose.json"

    result = export_viewer_pose(dataset, output)
    orientations = [frame["orientation"] for frame in result.document["frames"]]

    assert result.validation.overall_pass is True
    assert orientations == [
        [0.0, 0.0, 0.0, 1.0],
        [0.0, 0.0, 0.0, 1.0],
        [1.0, 0.0, 0.0, 0.0],
    ]


def test_pose_export_supports_xyzw_quaternions(tmp_path: Path) -> None:
    dataset = _write_fixture(
        tmp_path,
        quaternion_key="thorax_quaternions_xyzw",
        quaternions=np.asarray(
            [
                [0.0, 0.0, 0.0, 2.0],
                [0.0, 0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0, 0.0],
            ],
            dtype=float,
        ),
    )
    output = tmp_path / "viewer_pose.json"

    result = export_viewer_pose(dataset, output)

    assert result.validation.overall_pass is True
    assert result.document["metadata"]["input_quaternion_order"] == "xyzw"
    assert result.document["frames"][0]["orientation"] == [0.0, 0.0, 0.0, 1.0]


def test_cli_exports_pose_from_explicit_dataset_path(tmp_path: Path) -> None:
    dataset = _write_fixture(tmp_path)
    output = tmp_path / "cli" / "viewer_pose.json"
    script = Path(__file__).resolve().parents[1] / "scripts" / "export_viewer_pose.py"

    completed = subprocess.run(
        [sys.executable, str(script), "--dataset", str(dataset), "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(completed.stdout)["validation"]["overall_pass"] is True
    assert output.is_file()


def _write_fixture(
    tmp_path: Path,
    *,
    npz_name: str = "rollout_arrays.npz",
    time_s: np.ndarray | None = None,
    quaternion_key: str = "thorax_quaternions",
    quaternions: np.ndarray | None = None,
) -> Path:
    dataset = tmp_path / "Healthy_001"
    dataset.mkdir(parents=True)
    frames = [
        {
            "timestamp_s": 0.0,
            "step": 0,
            "thorax": [0.0, 0.0, 1.0],
            "com": [0.0, 0.0, 1.1],
            "orientation": [1.0, 0.0, 0.0, 0.0],
            "joint_positions": [0.0],
            "contact": {"LF": 1},
        },
        {
            "timestamp_s": 0.5,
            "step": 1,
            "thorax": [1.0, 0.0, 1.0],
            "com": [1.0, 0.0, 1.1],
            "orientation": [1.0, 0.0, 0.0, 0.0],
            "joint_positions": [1.0],
            "contact": {"LF": 0},
        },
        {
            "timestamp_s": 1.0,
            "step": 2,
            "thorax": [2.0, 0.5, 1.0],
            "com": [2.0, 0.5, 1.1],
            "orientation": [1.0, 0.0, 0.0, 0.0],
            "joint_positions": [2.0],
            "contact": {"LF": 1},
        },
    ]
    (dataset / "rollout.json").write_text(
        json.dumps({
            "schema_version": "flygym-rollout-1",
            "metadata": {
                "dataset_id": "Healthy_001",
                "timestep_s": 0.5,
                "joint_names": ["joint_a"],
                "body_segment_names": ["thorax", "head"],
            },
            "frames": frames,
        }),
        encoding="utf-8",
    )
    arrays = {
        "thorax_positions": np.asarray([frame["thorax"] for frame in frames], dtype=float),
        "body_positions": np.asarray(
            [
                [[0.0, 0.0, 1.0], [0.25, 0.0, 1.1]],
                [[1.0, 0.0, 1.0], [1.25, 0.0, 1.1]],
                [[2.0, 0.5, 1.0], [2.25, 0.5, 1.1]],
            ],
            dtype=float,
        ),
        quaternion_key: (
            np.asarray([frame["orientation"] for frame in frames], dtype=float)
            if quaternions is None
            else np.asarray(quaternions, dtype=float)
        ),
        "com_positions": np.asarray([frame["com"] for frame in frames], dtype=float),
        "joint_positions": np.asarray([[0.0], [1.0], [2.0]], dtype=float),
        "time_s": np.asarray([0.0, 0.5, 1.0], dtype=float) if time_s is None else np.asarray(time_s, dtype=float),
        "adhesion__LF": np.asarray([1, 0, 1], dtype=float),
    }
    np.savez_compressed(dataset / npz_name, **arrays)
    return dataset


def _pose_document() -> dict:
    return {
        "metadata": {},
        "fps": 2.0,
        "frame_count": 2,
        "joint_names": [],
        "mesh": {
            "renderer": "web/viewer/digital_fly_mesh.js",
            "render_mode": "procedural_fallback",
            "scientific_mesh": False,
            "visibility": {"mesh": True},
        },
        "frames": [
            {
                "frame_index": 0,
                "time": 0.0,
                "thorax": [0.0, 0.0, 1.0],
                "position": [0.0, 0.0, 1.0],
                "orientation": [0.0, 0.0, 0.0, 1.0],
                "COM": None,
                "joint_angles": {},
                "joint_velocity": {},
                "joint_acceleration": {},
                "contacts": {},
                "trajectory": {"thorax": [0.0, 0.0, 1.0]},
                "visibility": {"mesh": True, "skeleton": False, "COM": False, "trajectory": True},
            },
            {
                "frame_index": 1,
                "time": 0.5,
                "thorax": [1.0, 0.0, 1.0],
                "position": [1.0, 0.0, 1.0],
                "orientation": [0.0, 0.0, 0.0, 1.0],
                "COM": None,
                "joint_angles": {},
                "joint_velocity": {},
                "joint_acceleration": {},
                "contacts": {},
                "trajectory": {"thorax": [1.0, 0.0, 1.0]},
                "visibility": {"mesh": True, "skeleton": False, "COM": False, "trajectory": True},
            },
        ],
    }
