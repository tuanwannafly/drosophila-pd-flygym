from dataclasses import dataclass, field
from typing import Dict, Optional
from .metadata import ProjectMetadata
from .manifest import Manifest

@dataclass
class ProjectPackage:
    metadata: ProjectMetadata
    manifest: Manifest = field(default_factory=Manifest)
    scene_data: Dict = field(default_factory=dict)
    viewer_data: Dict = field(default_factory=dict)
    playback_data: Dict = field(default_factory=dict)
    preview_image: Optional[bytes] = None
    assets: Dict[str, bytes] = field(default_factory=dict)
