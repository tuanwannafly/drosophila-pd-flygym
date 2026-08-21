from dataclasses import dataclass
from typing import Any
from .asset_reference import AssetReference
from .asset_cache import AssetCache

@dataclass
class AssetLoader:
    """Lazy loader for assets."""
    cache: AssetCache

    def load(self, reference: AssetReference) -> Any:
        """Load asset, utilizing cache."""
        cached = self.cache.get(reference.id)
        if cached:
            return cached
        loaded_asset = {"data": "dummy"}
        self.cache.put(reference.id, loaded_asset)
        return loaded_asset
