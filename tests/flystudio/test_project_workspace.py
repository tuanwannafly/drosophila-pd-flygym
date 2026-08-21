from drosophila_pd.flystudio.project_workspace import ProjectWorkspace

def test_project_workspace():
    ws = ProjectWorkspace(id="ws1", metadata={"version": 1})
    assert ws.id == "ws1"
    assert ws.metadata["version"] == 1
