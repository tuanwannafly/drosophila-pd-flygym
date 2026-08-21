from dataclasses import dataclass

@dataclass
class PlaybackStatistics:
    """Statistics for playback performance and metrics."""
    frames_played: int = 0
    total_time: float = 0.0
    dropped_frames: int = 0

    def generate_report(self) -> str:
        return f"Played: {self.frames_played}, Dropped: {self.dropped_frames}, Time: {self.total_time}s"
