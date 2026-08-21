from dataclasses import dataclass

@dataclass
class ViewerState:
    """State of the digital fly studio viewer."""
    is_playing: bool = False
    current_time: float = 0.0
    show_skeleton: bool = True
    show_trajectory: bool = True
    show_grid: bool = True
    overlay_enabled: bool = False
    recording_active: bool = False
