from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class ProjectWorkspace:
    """Holds active projects and configs."""
    id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
