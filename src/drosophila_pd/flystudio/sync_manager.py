from dataclasses import dataclass
from .timeline_controller import TimelineController

@dataclass
class SyncManager:
    """Synchronizes multiple timelines."""
    master: TimelineController

    def sync(self, slave: TimelineController):
        slave.seek(self.master.current_time)
