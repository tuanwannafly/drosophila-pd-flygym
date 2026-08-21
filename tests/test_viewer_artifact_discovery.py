"""Tests for automatic discovery of generated viewer artifacts."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import time


ROOT = Path(__file__).parents[1]
_SCRIPT = ROOT / "scripts" / "run_demo.py"
_SPEC = importlib.util.spec_from_file_location("run_demo", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

from drosophila_pd.viewer_export import (  # noqa: E402
    find_latest_bundle,
    find_latest_rollout,
    find_latest_viewer_pose,
)


def test_discovery_selects_newest_complete_artifacts(tmp_path: Path) -> None:
    old = tmp_path / "old"
    new = tmp_path / "new"
    old.mkdir()
    new.mkdir()

    (old / "rollout.json").write_text(json.dumps({"frames": [1]}), encoding="utf-8")
    (old / "rollout.npz").write_bytes(b"old-rollout")
    (new / "rollout.json").write_text(json.dumps({"frames": [2]}), encoding="utf-8")
    (new / "rollout_arrays.npz").write_bytes(b"new-rollout")
    (old / "viewer_pose.json").write_text("{}", encoding="utf-8")
    (new / "viewer_pose.json").write_text("{}", encoding="utf-8")
    (old / "viewer_bundle.zip").write_bytes(b"old-bundle")
    (new / "viewer_bundle.zip").write_bytes(b"new-bundle")
    old_mtime = time.time_ns()
    new_mtime = old_mtime + 1_000_000_000
    for filename in ("rollout.json", "viewer_pose.json", "viewer_bundle.zip"):
        os.utime(old / filename, ns=(old_mtime, old_mtime))
        os.utime(new / filename, ns=(new_mtime, new_mtime))

    assert find_latest_rollout(tmp_path) == (new / "rollout.json").resolve()
    assert find_latest_viewer_pose(tmp_path) == (new / "viewer_pose.json").resolve()
    assert find_latest_bundle(tmp_path) == (new / "viewer_bundle.zip").resolve()

    (new / "rollout_arrays.npz").unlink()
    assert find_latest_rollout(tmp_path) == (old / "rollout.json").resolve()


def test_legacy_npz_alias_is_copied_without_changing_payload(tmp_path: Path) -> None:
    legacy = tmp_path / "rollout_arrays.npz"
    payload = b"recorded-rollout-array-payload"
    legacy.write_bytes(payload)

    canonical = _MODULE._ensure_legacy_npz_alias(tmp_path)

    assert canonical == tmp_path / "rollout.npz"
    assert canonical.read_bytes() == payload


def test_demo_manifest_creation_is_structural_only(tmp_path: Path) -> None:
    dataset = tmp_path / "Healthy_001"
    dataset.mkdir()
    (dataset / "rollout.json").write_text(
        json.dumps({"metadata": {"source": "test"}, "frames": [{"step": 0}]}),
        encoding="utf-8",
    )
    (dataset / "rollout.npz").write_bytes(b"recorded-array-payload")

    data, frames = _MODULE._rollout_payload(dataset / "rollout.json")
    _MODULE._write_metadata_and_manifest(dataset, data, frames)

    assert (dataset / "metadata.json").is_file()
    manifest = json.loads((dataset / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["frame_count"] == 1
    assert manifest["files"]["rollout.npz"]["sha256"]
