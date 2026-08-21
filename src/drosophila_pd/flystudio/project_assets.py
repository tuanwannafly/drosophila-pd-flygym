from dataclasses import dataclass, field
from typing import List
from .asset_database import AssetDatabase

@dataclass
class ProjectAssets:
    """Container for project-specific assets."""
    project_name: str
    database: AssetDatabase = field(default_factory=AssetDatabase)
    root_directories: List[str] = field(default_factory=list)
