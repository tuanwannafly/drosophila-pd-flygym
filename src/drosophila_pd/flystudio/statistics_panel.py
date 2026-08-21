from dataclasses import dataclass

@dataclass
class StatisticsPanel:
    """UI abstraction for rendering stats."""
    fps: float = 0.0
    frame_count: int = 0

    def update(self, fps: float, frame_count: int) -> None:
        self.fps = fps
        self.frame_count = frame_count
