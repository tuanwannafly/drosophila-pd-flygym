from dataclasses import dataclass, field
from .transform import Transform

@dataclass
class JointPose:
    """Pose of a single joint."""
    id: str
    transform: Transform = field(default_factory=Transform)
