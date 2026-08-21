from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class AnimationAsset:
    """Animation clip and timeline metadata."""
    id: str
    duration: float = 0.0
    clips: List[str] = field(default_factory=list)
    events: Dict[float, str] = field(default_factory=dict)
