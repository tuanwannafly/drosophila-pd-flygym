import json
from dataclasses import asdict
from .viewer_session import ViewerSession
from .viewer_state import ViewerState
from .viewer_layout import ViewerLayout

class ViewerSerializer:
    """Serializes the viewer session."""

    @staticmethod
    def serialize(session: ViewerSession) -> str:
        data = {
            "id": session.id,
            "state": asdict(session.state),
            "layout": asdict(session.layout)
        }
        return json.dumps(data)

    @staticmethod
    def deserialize(data: str) -> ViewerSession:
        parsed = json.loads(data)
        state = ViewerState(**parsed["state"])
        layout = ViewerLayout(**parsed["layout"])
        return ViewerSession(id=parsed["id"], state=state, layout=layout)
