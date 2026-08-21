from dataclasses import dataclass
from .viewer_state import ViewerState

@dataclass
class RecordingPanel:
    """UI abstraction for recording state."""
    state: ViewerState

    def start_recording(self) -> None:
        self.state.recording_active = True

    def stop_recording(self) -> None:
        self.state.recording_active = False
