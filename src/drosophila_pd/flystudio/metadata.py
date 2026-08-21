from dataclasses import dataclass, field
from typing import Dict, Any
from .versioning import Version

@dataclass
class ProjectMetadata:
    name: str
    author: str = "Unknown"
    version: Version = field(default_factory=lambda: Version(1, 0, 0))
    description: str = ""
    custom_data: Dict[str, Any] = field(default_factory=dict)
