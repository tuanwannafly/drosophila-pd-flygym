from dataclasses import dataclass
from typing import Optional

@dataclass
class MaterialAsset:
    """Renderer-independent material definition."""
    id: str
    albedo_texture_id: Optional[str] = None
    normal_texture_id: Optional[str] = None
    roughness: float = 0.5
    metallic: float = 0.0
