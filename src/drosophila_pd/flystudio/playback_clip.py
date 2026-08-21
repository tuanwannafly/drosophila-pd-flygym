from dataclasses import dataclass, field
from typing import List
from .playback_frame import PlaybackFrame

@dataclass
class PlaybackClip:
    """A collection of frames representing an animation clip."""
    id: str
    frames: List[PlaybackFrame] = field(default_factory=list)
    duration: float = 0.0
