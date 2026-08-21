from dataclasses import dataclass, field
from typing import List

@dataclass
class AssetBundle:
    """A collection of assets packaged together."""
    id: str
    asset_ids: List[str] = field(default_factory=list)
    compressed: bool = True
