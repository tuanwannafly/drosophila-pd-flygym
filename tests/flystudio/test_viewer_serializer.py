from drosophila_pd.flystudio.viewer_serializer import ViewerSerializer
from drosophila_pd.flystudio.viewer_session import ViewerSession

def test_viewer_serializer():
    session = ViewerSession(id="sess1")
    session.state.is_playing = True
    session.layout.split_type = "quad"

    data = ViewerSerializer.serialize(session)
    restored = ViewerSerializer.deserialize(data)

    assert restored.id == "sess1"
    assert restored.state.is_playing is True
    assert restored.layout.split_type == "quad"
