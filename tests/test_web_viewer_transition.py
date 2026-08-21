"""Contract checks for the additive pose-viewer transition layer."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
VIEWER = ROOT / "web" / "viewer"
VIEWER_FILES = (
    "pose_loader.js",
    "skeleton_animator.js",
    "camera_controller.js",
    "playback_controller.js",
    "scene_builder.js",
    "trajectory_renderer.js",
    "digital_fly_viewer.js",
    "digital_fly_scene.js",
    "digital_fly_mesh.js",
    "skeleton_renderer.js",
    "joint_animator.js",
    "lighting.js",
    "timeline_controller.js",
    "viewer.js",
)

THREE_VIEWER_FILES = {
    "camera_controller.js",
    "trajectory_renderer.js",
    "digital_fly_scene.js",
    "digital_fly_mesh.js",
    "skeleton_renderer.js",
    "joint_animator.js",
    "lighting.js",
    "viewer.js",
}


def test_viewer_files_exist_and_use_the_declared_rendering_layer() -> None:
    for filename in VIEWER_FILES:
        text = (VIEWER / filename).read_text(encoding="utf-8")
        assert "export" in text
        assert "babylon" not in text.lower()
        if filename in THREE_VIEWER_FILES:
            assert "three" in text.lower()


def test_pose_schema_is_explicit_and_data_free() -> None:
    schema_path = ROOT / "docs" / "api" / "viewer_pose.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    assert schema["required"] == ["metadata", "fps", "frame_count", "joint_names", "mesh", "frames"]
    mesh = schema["properties"]["mesh"]
    assert mesh["required"] == ["renderer", "render_mode", "scientific_mesh", "visibility"]
    frame_required = schema["properties"]["frames"]["items"]["required"]
    assert frame_required == [
        "frame_index",
        "time",
        "thorax",
        "position",
        "orientation",
        "COM",
        "joint_angles",
        "joint_velocity",
        "joint_acceleration",
        "contacts",
        "trajectory",
        "visibility",
    ]
    assert "example" not in schema


def test_rest_preparation_is_documentation_only() -> None:
    text = (ROOT / "docs" / "api" / "rest_api.md").read_text(encoding="utf-8")
    for endpoint in (
        "GET | `/datasets`",
        "GET | `/dataset/{id}`",
        "GET | `/rollout/{id}`",
        "GET | `/viewer/{id}`",
        "POST | `/analysis`",
        "POST | `/statistics`",
        "POST | `/validation`",
        "GET | `/report/{id}`",
    ):
        assert endpoint in text
    assert "no server implementation" in text.lower()


def test_three_viewer_is_integrated_without_replacing_canvas_scene_support() -> None:
    index = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    assert '"three": "https://cdn.jsdelivr.net/npm/three@0.180.0/' in index
    assert '"three/addons/": "https://cdn.jsdelivr.net/npm/three@0.180.0/' in index
    assert "new Viewer" in app
    assert "this.threeViewer.loadPose(rawData)" in app
    assert "this.threeViewer.setDigitalFly3D(this.digitalFly3D)" in app
    assert "this.viewportRenderer.canvas?.classList.add('hidden')" in app


def test_three_viewer_has_production_visual_controls_and_mesh_fallback_boundary() -> None:
    mesh = (VIEWER / "digital_fly_mesh.js").read_text(encoding="utf-8")
    scene = (VIEWER / "digital_fly_scene.js").read_text(encoding="utf-8")
    timeline = (VIEWER / "timeline_controller.js").read_text(encoding="utf-8")
    camera = (VIEWER / "camera_controller.js").read_text(encoding="utf-8")

    assert "GLTFLoader" in mesh
    assert "presentation fallback" in mesh
    assert "MeshStandardMaterial" in mesh
    assert "castShadow" in mesh
    assert "shadowMap.enabled = true" in (VIEWER / "viewer.js").read_text(encoding="utf-8")
    assert "setShadowEnabled" in scene
    assert "fitToPoints" in camera
    assert "demo" in camera
    for control in ("FPS", "Time", "Camera", "Axes", "Grid", "Floor", "Shadow"):
        assert control in timeline


def test_vietnamese_transition_documents_exist() -> None:
    for number, stem in (
        ("70", "Kien_Truc_Tong_The"),
        ("71", "Digital_Laboratory"),
        ("72", "Web_Viewer"),
        ("73", "Roadmap_Web"),
        ("74", "Module_Map"),
        ("75", "Cleanup_Report"),
    ):
        assert (ROOT / "docs" / "vi" / f"{number}_{stem}.md").is_file()
