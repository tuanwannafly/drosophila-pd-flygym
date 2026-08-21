from dataclasses import dataclass, field
from typing import Dict
from .skeleton_pose import SkeletonPose

@dataclass
class PoseCache:
    """Cache for retargeted poses."""
    max_size: int = 100
    _cache: Dict[float, SkeletonPose] = field(default_factory=dict)

    def get(self, time: float) -> SkeletonPose:
        return self._cache.get(time)

    def put(self, time: float, pose: SkeletonPose):
        if len(self._cache) >= self.max_size:
            first = next(iter(self._cache))
            del self._cache[first]
        self._cache[time] = pose
