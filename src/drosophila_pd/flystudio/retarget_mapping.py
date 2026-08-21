from dataclasses import dataclass, field
from .transform import Transform

@dataclass
class RetargetMapping:
    """Mapping from source playback data to target joints."""
    source_channel: str
    target_joint_id: str
    offset: Transform = field(default_factory=Transform)
    weight: float = 1.0
