from dataclasses import dataclass

@dataclass
class ViewerPreferences:
    """User preferences for the viewer."""
    theme: str = "dark"
    ui_scale: float = 1.0
    auto_play: bool = False
