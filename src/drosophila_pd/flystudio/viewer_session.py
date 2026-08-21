from dataclasses import dataclass, field
from .viewer_state import ViewerState
from .viewer_layout import ViewerLayout
from .project_workspace import ProjectWorkspace

@dataclass
class ViewerSession:
    """A full viewer session."""
    id: str
    state: ViewerState = field(default_factory=ViewerState)
    layout: ViewerLayout = field(default_factory=lambda: ViewerLayout(name="default"))
    workspace: ProjectWorkspace = None
