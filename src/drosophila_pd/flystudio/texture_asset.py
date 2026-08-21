from dataclasses import dataclass

@dataclass
class TextureAsset:
    """Texture image metadata."""
    id: str
    width: int = 0
    height: int = 0
    format: str = "RGBA8"
    mipmaps: bool = True
