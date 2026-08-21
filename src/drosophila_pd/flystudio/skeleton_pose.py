from dataclasses import dataclass, field
from typing import Dict
from .joint_pose import JointPose

@dataclass
class SkeletonPose:
    """Full pose for a skeleton."""
    id: str
    joints: Dict[str, JointPose] = field(default_factory=dict)
