from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class PlaybackFrame:
    """A single frame of playback data."""
    time: float
    data: Dict[str, Any]
