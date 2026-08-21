import json
from dataclasses import dataclass
from typing import Dict, Any

class PlaybackSerializer:
    """Serializes playback sessions."""

    @staticmethod
    def serialize(session: Any) -> str:
        return json.dumps({"session_id": session.id, "duration": session.duration})

    @staticmethod
    def deserialize(data: str) -> Dict[str, Any]:
        return json.loads(data)
