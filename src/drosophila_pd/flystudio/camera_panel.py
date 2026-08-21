from dataclasses import dataclass

@dataclass
class CameraPreset:
    name: str
    target: str
    zoom: float

@dataclass
class CameraPanel:
    """UI abstraction for camera controls."""
    current_preset: CameraPreset = None
    tracking_enabled: bool = False

    def apply_preset(self, preset: CameraPreset) -> None:
        self.current_preset = preset
