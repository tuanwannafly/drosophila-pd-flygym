from dataclasses import dataclass, field
from typing import List
from .playback_track import PlaybackTrack

@dataclass
class TimelineController:
    """Controls the playback timeline and tracks."""
    current_time: float = 0.0
    duration: float = 0.0
    tracks: List[PlaybackTrack] = field(default_factory=list)

    def seek(self, time: float) -> None:
        self.current_time = max(0.0, min(time, self.duration))
