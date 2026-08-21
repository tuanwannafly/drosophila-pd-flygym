from dataclasses import dataclass, field
from typing import List

@dataclass
class ViewerLayout:
    """Defines the viewport layout presets."""
    name: str
    split_type: str = "single"
    viewport_ids: List[str] = field(default_factory=lambda: ["main"])
