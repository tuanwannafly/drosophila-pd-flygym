from dataclasses import dataclass

@dataclass
class MeshAsset:
    """Mesh asset metadata (no geometry processing)."""
    id: str
    vertices_count: int = 0
    normals_count: int = 0
    uv_count: int = 0
    has_tangents: bool = False
