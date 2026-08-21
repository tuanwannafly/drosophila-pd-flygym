from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"


def test_digital_laboratory_model_contract():
    text = (WEB / "digital_laboratory.js").read_text(encoding="utf-8")
    required = [
        "DigitalLaboratory",
        "EntityStore",
        "createProject",
        "addSubject",
        "addTrial",
        "addExperiment",
        "createAnalysisSession",
        "createNotebook",
        "createPublicationBundle",
        "setCollaboration",
        "dashboard",
        "browse",
        "toJSON",
        "restore",
        "experimentWorkspace",
        "scientificScope",
    ]
    assert all(marker in text for marker in required)


def test_app_exposes_laboratory_without_replacing_existing_workspace():
    text = (WEB / "app.js").read_text(encoding="utf-8")
    assert "DigitalLaboratory" in text
    assert "this.experimentWorkspace = new ExperimentWorkspace()" in text
    assert "this.laboratory = new DigitalLaboratory" in text


def test_vietnamese_epic_13_documentation_exists():
    required = [
        "13_Phong_thi_nghiem_so.md",
        "14_Quan_ly_Du_an.md",
        "15_Huong_dan_Phan_tich.md",
        "16_Huong_dan_Xuat_Bao_cao.md",
        "17_Cau_truc_Phong_thi_nghiem.md",
    ]
    docs = ROOT / "docs" / "vi"
    assert all((docs / name).exists() for name in required)
    assert (docs / "milestones" / "epic_13_digital_laboratory.md").exists()
