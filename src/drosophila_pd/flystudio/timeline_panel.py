from dataclasses import dataclass
from .viewer_state import ViewerState

@dataclass
class TimelinePanel:
    """UI abstraction for timeline."""
    state: ViewerState

    def seek(self, time: float) -> None:
        self.state.current_time = time
