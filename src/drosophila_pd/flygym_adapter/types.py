"""Backend-neutral types for FlyGym observations and exported rollouts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


def _json_value(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


@dataclass
class ObservationFrame:
    """One observation captured from a real FlyGym simulation step."""

    timestamp_s: float
    step: int
    thorax: np.ndarray | None
    com: np.ndarray | None
    orientation: np.ndarray | None
    body_positions: np.ndarray | None
    body_orientations: np.ndarray | None
    joint_positions: np.ndarray | None
    joint_velocity: np.ndarray | None
    joint_acceleration: np.ndarray | None
    contact: dict[str, Any] | None
    actuator: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp_s": float(self.timestamp_s),
            "step": int(self.step),
            "thorax": _json_value(self.thorax),
            "com": _json_value(self.com),
            "orientation": _json_value(self.orientation),
            "body_positions": _json_value(self.body_positions),
            "body_orientations": _json_value(self.body_orientations),
            "joint_positions": _json_value(self.joint_positions),
            "joint_velocity": _json_value(self.joint_velocity),
            "joint_acceleration": _json_value(self.joint_acceleration),
            "contact": _json_value(self.contact),
            "actuator": _json_value(self.actuator),
        }


@dataclass
class RolloutData:
    """Recorded observation sequence plus simulation provenance metadata."""

    frames: list[ObservationFrame] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = "flygym-rollout-1"

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "metadata": _json_value(self.metadata),
            "frames": [frame.to_dict() for frame in self.frames],
        }


@dataclass(frozen=True)
class ExportedRollout:
    """Paths and manifest returned by the rollout exporter."""

    output_dir: str
    files: dict[str, str]
    manifest: dict[str, Any]


__all__ = ["ExportedRollout", "ObservationFrame", "RolloutData"]
