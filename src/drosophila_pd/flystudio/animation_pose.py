from dataclasses import dataclass, field
from typing import List
from .skeleton_pose import SkeletonPose

@dataclass
class AnimationPose:
    """Container for blended animation poses."""
    base_pose: SkeletonPose
    layers: List[SkeletonPose] = field(default_factory=list)
