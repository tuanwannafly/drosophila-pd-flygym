from pathlib import Path


ROOT = Path(__file__).parents[1]
WEB = ROOT / "web"
VI = ROOT / "docs" / "vi"


def test_research_workbench_contract_is_additive_and_input_driven():
    workbench = (WEB / "research_workbench.js").read_text(encoding="utf-8")
    panel = (WEB / "research_workbench_panel.js").read_text(encoding="utf-8")
    app = (WEB / "app.js").read_text(encoding="utf-8")
    assert "WorkbenchLayoutManager" in workbench
    assert "ResearchNotebook" in workbench
    assert "ValidationCenter" in workbench
    assert "ProjectBundleManager" in workbench
    assert "no biological" in (workbench + panel).lower()
    assert "research-workbench" in app
    assert "workspace.currentFrame" in app
    assert "setSynchronization" in panel


def test_research_workbench_keeps_scientific_and_simulation_paths_out_of_scope():
    changed = {
        path.as_posix()
        for path in ROOT.glob("web/research_workbench*.js")
    }
    assert changed
    assert not any(path.startswith(("src/", "results/", "notebooks/", "docs/report/")) for path in changed)


def test_research_workbench_documentation_exists():
    required = {
        "57_Workbench.md",
        "58_Workspace.md",
        "59_Validation_Center.md",
        "60_Publication_Workspace.md",
        "61_Research_Notebook.md",
        "62_Project_Bundle.md",
    }
    assert required <= {path.name for path in VI.glob("*.md")}
