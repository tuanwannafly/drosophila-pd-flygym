from dataclasses import dataclass, field
from typing import List
from .playback_clip import PlaybackClip

@dataclass
class PlaybackTrack:
    """A track containing multiple clips over time."""
    id: str
    clips: List[PlaybackClip] = field(default_factory=list)
