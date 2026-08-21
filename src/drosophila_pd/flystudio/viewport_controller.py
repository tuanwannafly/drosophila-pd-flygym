from dataclasses import dataclass
from .viewer_state import ViewerState

@dataclass
class ViewportController:
    """Controls a single viewport."""
    id: str
    state: ViewerState

    def toggle_skeleton(self) -> None:
        self.state.show_skeleton = not self.state.show_skeleton

    def toggle_grid(self) -> None:
        self.state.show_grid = not self.state.show_grid
