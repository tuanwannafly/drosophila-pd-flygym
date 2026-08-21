from dataclasses import dataclass
from .asset_database import AssetDatabase
from .asset_loader import AssetLoader

@dataclass
class ResourceManager:
    """Central manager for asset lifecycle."""
    database: AssetDatabase
    loader: AssetLoader

    def get_resource(self, uuid: str):
        asset = self.database.get_asset(uuid)
        if asset:
            return asset
        return None
