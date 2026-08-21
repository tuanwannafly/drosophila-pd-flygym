from dataclasses import dataclass
from typing import Optional

@dataclass
class AssetReference:
    """Reference to an asset."""
    id: str
    relative_path: str = ""
    external_path: str = ""
    virtual_path: str = ""
    resolved_path: Optional[str] = None
