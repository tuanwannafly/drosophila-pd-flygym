from __future__ import annotations

import json
import importlib.util
from pathlib import Path
import zipfile

import numpy as np
import pytest

from drosophila_pd.flygym_adapter import (
    FlyGymAdapter,
    FlyGymConfig,
    FlyGymUnavailableError,
    RolloutRecorder,
    export_rollout,
)
from drosophila_pd.viewer_export import export_viewer_pose, validate_pose_document


REPO_ROOT = Path(__file__).resolve().parents[1]
_BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_viewer_bundle.py"
_BUILD_SPEC = importlib.util.spec_from_file_location("build_viewer_bundle", _BUILD_SCRIPT)
assert _BUILD_SPEC is not None and _BUILD_SPEC.loader is not None
_BUILD_MODULE = importlib.util.module_from_spec(_BUILD_SPEC)
_BUILD_SPEC.loader.exec_module(_BUILD_MODULE)
build_bundle = _BUILD_MODULE.build_bundle


def test_real_flygym_rollout_exports_valid_viewer_pose_if_available(tmp_path: Path) -> None:
    """Run the real FlyGym rollout-to-viewer path when FlyGym/MuJoCo exist.

    This is an integration test, not a mocked contract test. It automatically
    skips in lightweight CI environments that do not install the simulator stack.
    """

    _skip_unless_flygym_runtime_available()
    config = FlyGymConfig.from_yaml(
        REPO_ROOT / "configs" / "v2" / "flygym" / "healthy.yaml"
    )
    adapter = FlyGymAdapter()
    simulation = None
    try:
        fly = adapter.create_fly(config.fly)
        world = adapter.create_world(config.world)
        adapter.attach_fly(
            world,
            fly,
            position=config.world.spawn_position,
            orientation=config.world.spawn_orientation,
            add_ground_contact_sensors=config.world.add_ground_contact_sensors,
        )
        simulation = adapter.create_simulation(world, config.simulation)
        simulation.reset()

        recorder = RolloutRecorder(
            simulation,
            fly.name,
            fly=fly,
            timestep=float(getattr(simulation, "timestep", config.simulation.timestep)),
            simulation_metadata=config.to_mapping(),
        )
        for _ in range(100):
            simulation.step()
            recorder.record()
    except FlyGymUnavailableError as exc:
        pytest.skip(str(exc))
    finally:
        close = getattr(simulation, "close", None)
        if callable(close):
            close()

    assert recorder.rollout.frame_count == 100
    first_orientation = np.asarray(recorder.rollout.frames[0].orientation, dtype=float)
    assert np.linalg.norm(first_orientation) > 0.0

    dataset_dir = tmp_path / "datasets" / "healthy" / "Healthy_001"
    exported = export_rollout(recorder.rollout, dataset_dir)
    assert Path(exported.files["rollout_json"]).is_file()
    assert Path(exported.files["rollout_npz"]).is_file()

    result = export_viewer_pose(
        "Healthy_001",
        tmp_path / "viewer_pose.json",
        search_roots=[tmp_path / "datasets"],
    )

    assert result.output_path.is_file()
    assert result.validation.overall_pass is True
    assert (
        validate_pose_document(result.document, expected_frame_count=100).overall_pass
        is True
    )
    assert result.document["frame_count"] == 100

    frame_times = np.asarray(
        [frame["time"] for frame in result.document["frames"]],
        dtype=float,
    )
    assert np.all(np.diff(frame_times) > 0.0)

    orientations = np.asarray(
        [frame["orientation"] for frame in result.document["frames"]],
        dtype=float,
    )
    assert np.linalg.norm(orientations[0]) > 0.0
    assert np.allclose(np.linalg.norm(orientations, axis=1), 1.0, atol=1e-6)

    bundle_dir, bundle_archive, manifest = build_bundle(
        result.output_path,
        output=tmp_path / "dist" / "viewer_bundle.zip",
    )
    assert bundle_archive.is_file()
    assert (bundle_dir / "index.html").is_file()
    assert (bundle_dir / "viewer_pose.json").is_file()
    assert (bundle_dir / "viewer" / "viewer.js").is_file()
    assert manifest["entrypoint"] == "index.html"
    with zipfile.ZipFile(bundle_archive) as archive:
        names = set(archive.namelist())
        assert "viewer_bundle/index.html" in names
        assert "viewer_bundle/viewer_pose.json" in names
        extracted_pose = json.loads(archive.read("viewer_bundle/viewer_pose.json"))
    assert validate_pose_document(extracted_pose, expected_frame_count=100).overall_pass


def _skip_unless_flygym_runtime_available() -> None:
    pytest.importorskip("flygym", reason="FlyGym/MuJoCo integration test requires FlyGym.")
    pytest.importorskip("mujoco", reason="FlyGym/MuJoCo integration test requires MuJoCo.")
    pytest.importorskip(
        "flygym_demo",
        reason="Canonical locomotion fly integration requires flygym_demo.",
    )
