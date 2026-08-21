from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class AssetDatabase:
    """Database of all available assets."""
    assets: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"
    tags: Dict[str, List[str]] = field(default_factory=dict)

    def register_asset(self, uuid: str, asset: Any, asset_tags: List[str] = None) -> None:
        self.assets[uuid] = asset
        if asset_tags:
            self.tags[uuid] = asset_tags

    def get_asset(self, uuid: str) -> Any:
        return self.assets.get(uuid)
