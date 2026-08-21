from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
DOCS = ROOT / "docs" / "vi"


def test_interactive_viewer_contract_is_present_and_input_driven():
    camera = (WEB / "camera.js").read_text(encoding="utf-8")
    renderer = (WEB / "digital_fly_3d_renderer.js").read_text(encoding="utf-8")
    viewport = (WEB / "viewport_renderer.js").read_text(encoding="utf-8")
    toolbar = (WEB / "toolbar.js").read_text(encoding="utf-8")
    comparison = (WEB / "comparison_viewer.js").read_text(encoding="utf-8")
    for marker in ("CAMERA_TYPES", "CAMERA_PRESETS", "orthographic", "setPreset", "orbit"):
        assert marker in camera
    for marker in ("drawBodyMesh", "bodyPartVisibility", "drawMotionVectors", "hitTest", "drawContacts"):
        assert marker in renderer
    for marker in ("setCameraType", "setCameraPreset", "focusBodyPart", "exportPNG", "onSelect"):
        assert marker in viewport
    for marker in ("camera-type-input", "camera-preset-input", "focus-selected-button", "export-view-png-button"):
        assert marker in toolbar
    for marker in ("comparison-canvas", "comparison-frame-slider", "drawCanvases"):
        assert marker in comparison


def test_interactive_viewer_does_not_touch_scientific_runtime():
    for filename in ("camera.js", "digital_fly_3d_renderer.js", "viewport_renderer.js"):
        text = (WEB / filename).read_text(encoding="utf-8").lower()
        assert "add_joints" not in text
        assert "mujoco" not in text


def test_vietnamese_viewer_documentation_exists():
    required = (
        "51_3D_Viewer.md",
        "52_Digital_Fly.md",
        "53_Che_Do_So_Sanh.md",
        "54_Overlay_Khoa_Hoc.md",
        "55_Ghi_Hinh_Va_Xuat_Anh.md",
        "56_Huong_Dan_3D.md",
    )
    assert all((DOCS / name).exists() for name in required)
