from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
DOCS = ROOT / "docs" / "vi"


def test_3d_motion_engine_contract():
    text = (WEB / "digital_fly_3d.js").read_text(encoding="utf-8")
    required = [
        "DigitalFly3D",
        "Skeleton3D",
        "Bone3D",
        "Joint3D",
        "DEFAULT_FLY_SKELETON",
        "updateWorldTransforms",
        "applyTrajectoryFrame",
        "interpolateTransform",
        "interpolatePose",
        "blendPoses",
        "slerpQuaternions",
        "computeSkeletonMetrics",
        "validateSkeleton3D",
        "validateTrajectoryOwnership",
        "flyId",
    ]
    assert all(marker in text for marker in required)


def test_3d_renderer_contract_and_app_integration():
    renderer = (WEB / "digital_fly_3d_renderer.js").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")
    viewport = (WEB / "viewport_renderer.js").read_text(encoding="utf-8")
    for marker in [
        "DigitalFly3DRenderer",
        "drawGround",
        "drawAxes",
        "drawTrajectory",
        "drawSkeleton",
        "drawJointAxis",
        "drawCOM",
        "orbitYaw",
        "orbitPitch",
    ]:
        assert marker in renderer or marker in viewport
    assert "DigitalFly3D.fromDigitalFly" in app
    assert "setDigitalFly3D" in app
    assert "DigitalFly3DRenderer" in viewport


def test_epic_15_documentation_exists():
    required = [
        "18_Mo_hinh_Con_Ruoi_So.md",
        "19_Khung_Xuong_3D.md",
        "20_Dong_Hoc_Thuan.md",
        "21_Dieu_Khien_Chuyen_Dong.md",
        "22_He_Toa_Do_3D.md",
        "23_Huong_Dan_3D_Viewer.md",
    ]
    assert all((DOCS / name).exists() for name in required)
    assert (DOCS / "milestones" / "epic_15_3d_motion_engine.md").exists()


def test_epic_15_does_not_touch_frozen_python_simulation_modules():
    model = (WEB / "digital_fly_3d.js").read_text(encoding="utf-8").lower()
    renderer = (WEB / "digital_fly_3d_renderer.js").read_text(encoding="utf-8").lower()
    assert "add_joints" not in model
    assert "mujoco" not in model
    assert "import " not in renderer
    assert "add_joints" not in renderer
    assert "mujoco" not in renderer
