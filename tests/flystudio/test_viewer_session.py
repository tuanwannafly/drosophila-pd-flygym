from drosophila_pd.flystudio.viewer_session import ViewerSession
from drosophila_pd.flystudio.viewer_layout import ViewerLayout
from drosophila_pd.flystudio.project_workspace import ProjectWorkspace

def test_viewer_session():
    ws = ProjectWorkspace(id="ws1")
    session = ViewerSession(id="sess1", workspace=ws)

    assert session.id == "sess1"
    assert session.workspace.id == "ws1"
    assert session.layout.name == "default"
    assert session.state.is_playing is False
