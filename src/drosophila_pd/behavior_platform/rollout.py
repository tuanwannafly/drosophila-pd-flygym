"""Typed rollout containers for v2 behavioral post-processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np


ArrayLike = Sequence[float] | Sequence[Sequence[float]] | np.ndarray


@dataclass(frozen=True)
class RolloutData:
    """Canonical v2 representation of one already-produced rollout.

    The container stores arrays and metadata only. It intentionally has no
    FlyGym, MuJoCo, controller, perturbation, or simulation ownership.
    """

    condition_id: str
    timestep_s: float
    thorax_positions: ArrayLike
    thorax_quaternions: ArrayLike
    sample_id: str | None = None
    com_positions: ArrayLike | None = None
    joint_positions: Mapping[str, ArrayLike] | None = None
    adhesion_outputs: Mapping[str, ArrayLike] | None = None
    frames: Sequence[Any] | np.ndarray | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def positions_array(self) -> np.ndarray:
        return _matrix("thorax_positions", self.thorax_positions, 3)

    def quaternions_array(self) -> np.ndarray:
        return _matrix("thorax_quaternions", self.thorax_quaternions, 4)

    def com_array(self) -> np.ndarray | None:
        if self.com_positions is None:
            return None
        return _matrix("com_positions", self.com_positions, 3)

    def joint_arrays(self) -> dict[str, np.ndarray]:
        return _mapping_to_arrays(self.joint_positions or {}, "joint_positions")

    def adhesion_arrays(self) -> dict[str, np.ndarray]:
        return _mapping_to_arrays(self.adhesion_outputs or {}, "adhesion_outputs")

    def timestep(self) -> float:
        value = float(self.timestep_s)
        if not np.isfinite(value) or value <= 0:
            raise ValueError("timestep_s must be a positive finite number.")
        return value

    def sample_count(self) -> int:
        positions = self.positions_array()
        quaternions = self.quaternions_array()
        if positions.shape[0] != quaternions.shape[0]:
            raise ValueError("thorax position and quaternion sample counts must match.")
        com = self.com_array()
        if com is not None and com.shape[0] != positions.shape[0]:
            raise ValueError("com_positions sample count must match thorax positions.")
        for name, array in self.joint_arrays().items():
            if array.shape[0] != positions.shape[0]:
                raise ValueError(f"joint_positions[{name!r}] sample count mismatch.")
        for name, array in self.adhesion_arrays().items():
            if array.shape[0] != positions.shape[0]:
                raise ValueError(f"adhesion_outputs[{name!r}] sample count mismatch.")
        return int(positions.shape[0])

    def time_s(self) -> np.ndarray:
        return np.arange(self.sample_count(), dtype=float) * self.timestep()

    def as_metadata(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "sample_id": self.sample_id,
            "sample_count": self.sample_count(),
            "timestep_s": self.timestep(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RolloutData":
        """Build a rollout from a JSON-like mapping."""

        return cls(
            condition_id=str(data["condition_id"]),
            sample_id=data.get("sample_id"),
            timestep_s=float(data["timestep_s"]),
            thorax_positions=data["thorax_positions"],
            thorax_quaternions=data["thorax_quaternions"],
            com_positions=data.get("com_positions"),
            joint_positions=data.get("joint_positions"),
            adhesion_outputs=data.get("adhesion_outputs"),
            frames=data.get("frames"),
            metadata=data.get("metadata", {}),
        )


def _matrix(name: str, value: ArrayLike, width: int) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or array.shape[1] != width:
        raise ValueError(f"{name} must have shape (n_samples, {width}).")
    if array.shape[0] == 0 or not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite samples.")
    return array


def _mapping_to_arrays(values: Mapping[str, ArrayLike], name: str) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for key, value in values.items():
        array = np.asarray(value, dtype=float)
        if array.ndim == 0 or array.shape[0] == 0 or not np.isfinite(array).all():
            raise ValueError(f"{name}[{key!r}] must contain finite samples.")
        arrays[str(key)] = array
    return arrays


__all__ = ["ArrayLike", "RolloutData"]
