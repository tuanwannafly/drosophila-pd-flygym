from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class TrajectoryAsset:
    """Trajectory replay metadata."""
    id: str
    frame_count: int = 0
    frame_rate: float = 30.0
    metadata: Dict[str, Any] = None
