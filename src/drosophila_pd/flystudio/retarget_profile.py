from dataclasses import dataclass, field
from typing import List
from .retarget_mapping import RetargetMapping
from .transform import Transform

@dataclass
class RetargetProfile:
    """Profile containing rules for motion retargeting."""
    id: str
    mappings: List[RetargetMapping] = field(default_factory=list)
    root_transform: Transform = field(default_factory=Transform)
