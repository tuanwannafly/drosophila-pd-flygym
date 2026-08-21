"""Regression tests for static viewer bundle creation and local serving."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen
import zipfile


ROOT = Path(__file__).parents[1]


def _pose_document() -> dict:
    return {
        "metadata": {"dataset_id": "Healthy_001", "quaternion_order": "xyzw"},
        "fps": 100.0,
        "frame_count": 1,
        "joint_names": [],
        "mesh": {
            "renderer": "web/viewer/digital_fly_mesh.js",
            "render_mode": "procedural_fallback",
            "scientific_mesh": False,
            "visibility": {"mesh": True, "skeleton": False, "trajectory": True, "COM": False},
        },
        "frames": [{
            "frame_index": 0,
            "time": 0.0,
            "thorax": [0.0, 0.0, 0.5],
            "position": [0.0, 0.0, 0.5],
            "orientation": [0.0, 0.0, 0.0, 1.0],
            "COM": None,
            "joint_angles": {},
            "joint_velocity": {},
            "joint_acceleration": {},
            "joint_velocities": {},
            "contacts": {},
            "trajectory": {"thorax": [0.0, 0.0, 0.5], "COM": None, "joints": {}},
            "skeleton": None,
            "visibility": {"mesh": True, "skeleton": False, "trajectory": True, "COM": False},
        }],
    }


def test_build_viewer_bundle_contains_static_entrypoint_and_pose(tmp_path: Path) -> None:
    pose = tmp_path / "viewer_pose.json"
    pose.write_text(json.dumps(_pose_document()), encoding="utf-8")
    archive = tmp_path / "dist" / "viewer_bundle.zip"
    command = [
        sys.executable,
        "scripts/build_viewer_bundle.py",
        "--pose",
        str(pose),
        "--output",
        str(archive),
    ]
    subprocess.run(command, cwd=ROOT, check=True)

    stage = archive.parent / "viewer_bundle"
    assert (stage / "index.html").is_file()
    assert (stage / "viewer_pose.json").is_file()
    assert (stage / "viewer" / "viewer.js").is_file()
    assert (stage / "web" / "index.html").is_file()
    manifest = json.loads((stage / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["entrypoint"] == "index.html"
    assert any(item["path"] == "viewer_pose.json" for item in manifest["files"])

    with zipfile.ZipFile(archive) as bundle:
        names = set(bundle.namelist())
    assert "viewer_bundle/index.html" in names
    assert "viewer_bundle/viewer_pose.json" in names
    assert "viewer_bundle/viewer/viewer.js" in names
    assert "viewer_bundle/web/index.html" in names


def test_run_viewer_serves_pose_without_copying_it_into_web(tmp_path: Path) -> None:
    pose = tmp_path / "viewer_pose.json"
    pose.write_text(json.dumps(_pose_document()), encoding="utf-8")
    ready = tmp_path / "ready.txt"
    process = subprocess.Popen(
        [
            sys.executable,
            "scripts/run_viewer.py",
            "--pose",
            str(pose),
            "--port",
            "0",
            "--no-browser",
            "--quiet",
            "--ready-file",
            str(ready),
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not ready.exists():
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise AssertionError(f"viewer server exited: {output}")
            time.sleep(0.05)
        assert ready.exists()
        base = ready.read_text(encoding="utf-8").strip()
        with urlopen(base, timeout=5) as response:
            assert response.status == 200
            assert b"Fly Studio Viewer" in response.read()
        with urlopen(base.replace("/index.html", "/viewer_pose.json"), timeout=5) as response:
            assert json.loads(response.read()) == _pose_document()
    finally:
        process.terminate()
        process.wait(timeout=10)
