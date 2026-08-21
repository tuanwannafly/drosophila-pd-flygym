from dataclasses import dataclass
from typing import Callable, List

@dataclass
class FrameScheduler:
    """Schedules callbacks on specific frames."""
    callbacks: List[Callable]

    def execute_frame(self, frame_index: int):
        for callback in self.callbacks:
            callback(frame_index)
