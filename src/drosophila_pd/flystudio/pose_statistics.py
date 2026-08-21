from dataclasses import dataclass

@dataclass
class PoseStatistics:
    """Statistics for retargeting operations."""
    poses_generated: int = 0
    cache_hits: int = 0
    validation_errors: int = 0

    def report(self) -> str:
        return f"Poses: {self.poses_generated}, Hits: {self.cache_hits}, Errors: {self.validation_errors}"
