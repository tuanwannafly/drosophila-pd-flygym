from typing import List, Dict, Any
from .playback_frame import PlaybackFrame
from .playback_clip import PlaybackClip

class KeyframeBuilder:
    """Builds keyframes from raw data."""

    @staticmethod
    def build_clip(clip_id: str, times: List[float], data_points: List[Dict[str, Any]]) -> PlaybackClip:
        frames = [PlaybackFrame(time=t, data=d) for t, d in zip(times, data_points)]
        duration = times[-1] if times else 0.0
        return PlaybackClip(id=clip_id, frames=frames, duration=duration)
