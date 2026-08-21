from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
DOCS = ROOT / "docs" / "vi"


def test_digital_fly_model_contract():
    text = (WEB / "digital_fly.js").read_text(encoding="utf-8")
    required = [
        "DigitalFly",
        "BodyModel",
        "SkeletonModel",
        "JointModel",
        "WingModel",
        "LegModel",
        "HeadModel",
        "COMModel",
        "OrientationModel",
        "PoseModel",
        "MotionModel",
        "ParkinsonStateModel",
        "TrajectoryRegistry",
        "trajectoryRefs",
        "metadata: clone(this.metadata)",
        "fromRollout",
        "ingestRollout",
        "attachTrajectory",
        "validate",
        "toJSON",
        "fromJSON",
        "flyId",
    ]
    assert all(marker in text for marker in required)


def test_rollout_integration_registers_digital_fly_without_changing_loader():
    app = (WEB / "app.js").read_text(encoding="utf-8")
    laboratory = (WEB / "digital_laboratory.js").read_text(encoding="utf-8")
    assert "DigitalFly.fromRollout(rollout" in app
    assert "this.digitalFly = null" in app
    assert "registerFly(this.digitalFly)" in app
    assert "registerFly(fly" in laboratory
    assert "digitalFlies" in laboratory


def test_digital_fly_documentation_exists():
    required = [
        "18_Digital_Fly.md",
        "19_Huong_dan_Digital_Fly.md",
        "20_Mo_hinh_Du_lieu_Fly.md",
        "21_Trajectory_va_Fly.md",
        "22_Trang_thai_Parkinson.md",
    ]
    assert all((DOCS / name).exists() for name in required)
    assert (DOCS / "milestones" / "epic_14_digital_fly.md").exists()
