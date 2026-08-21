from dataclasses import dataclass
from .viewer_state import ViewerState

@dataclass
class PlaybackPanel:
    """UI abstraction for playback."""
    state: ViewerState

    def play(self) -> None:
        self.state.is_playing = True

    def pause(self) -> None:
        self.state.is_playing = False
