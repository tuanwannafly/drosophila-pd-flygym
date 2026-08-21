from dataclasses import dataclass, field
from typing import Dict

@dataclass
class EventTrack:
    """Track for playback events and bookmarks."""
    id: str
    events: Dict[float, str] = field(default_factory=dict)
    bookmarks: Dict[float, str] = field(default_factory=dict)

    def add_event(self, time: float, name: str):
        self.events[time] = name

    def add_bookmark(self, time: float, name: str):
        self.bookmarks[time] = name
