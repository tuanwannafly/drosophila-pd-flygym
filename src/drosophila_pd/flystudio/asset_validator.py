from dataclasses import dataclass
from typing import List
from .asset_database import AssetDatabase

@dataclass
class AssetValidator:
    """Validates asset dependencies and integrity."""
    database: AssetDatabase

    def validate(self) -> List[str]:
        """Returns a list of validation errors."""
        errors = []
        ids = set()
        for uuid, asset in self.database.assets.items():
            if uuid in ids:
                errors.append(f"Duplicate ID found: {uuid}")
            ids.add(uuid)
            if not asset:
                errors.append(f"Asset missing data: {uuid}")
        return errors
