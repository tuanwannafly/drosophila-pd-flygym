from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class PlaybackCache:
    """Cache for pre-computed playback frames."""
    max_frames: int = 1000
    frames: Dict[float, Any] = field(default_factory=dict)

    def get_frame(self, time: float) -> Any:
        return self.frames.get(time)

    def store_frame(self, time: float, data: Any):
        if len(self.frames) >= self.max_frames:
            first_key = next(iter(self.frames))
            del self.frames[first_key]
        self.frames[time] = data
