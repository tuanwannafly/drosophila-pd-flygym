from dataclasses import dataclass, field
from .timeline_controller import TimelineController
from .motion_player import MotionPlayer
from .playback_statistics import PlaybackStatistics

@dataclass
class PlaybackSession:
    """A full playback session package."""
    id: str
    duration: float = 0.0
    timeline: TimelineController = field(default_factory=TimelineController)
    player: MotionPlayer = None
    stats: PlaybackStatistics = field(default_factory=PlaybackStatistics)

    def __post_init__(self):
        if self.player is None:
            self.player = MotionPlayer(timeline=self.timeline)
