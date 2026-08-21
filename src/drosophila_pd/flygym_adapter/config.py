"""Configuration models for the verified FlyGym adapter surface."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml


@dataclass(frozen=True)
class FlyConfig:
    """Fly construction settings.

    ``canonical_locomotion`` delegates to the repository's existing official
    FlyGym demo helper when it is installed. ``neuromechfly`` uses the public
    FlyGym 2.1.0 ``NeuroMechFly`` constructor directly.
    """

    name: str = "healthy_baseline"
    factory: str = "canonical_locomotion"
    model_kwargs: dict[str, Any] = field(default_factory=dict)
    locomotion_kwargs: dict[str, Any] = field(default_factory=lambda: {
        "joint_stiffness": 0.05,
        "joint_damping": 0.06,
        "passive_tarsus_stiffness": 7.5,
        "passive_tarsus_damping": 0.01,
        "actuator_gain": 45.0,
        "actuator_forcerange": (-65.0, 65.0),
        "add_adhesion": True,
        "adhesion_gain": 40.0,
        "colorize": False,
    })

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any] | None) -> "FlyConfig":
        values = dict(mapping or {})
        locomotion = dict(cls().locomotion_kwargs)
        locomotion.update(values.pop("locomotion_kwargs", {}) or {})
        return cls(
            name=str(values.pop("name", "healthy_baseline")),
            factory=str(values.pop("factory", "canonical_locomotion")),
            model_kwargs=dict(values.pop("model_kwargs", {}) or {}),
            locomotion_kwargs=locomotion,
        )

    def validate(self) -> None:
        if not self.name:
            raise ValueError("fly.name must not be empty")
        if self.factory not in {"canonical_locomotion", "neuromechfly"}:
            raise ValueError(f"Unsupported fly factory: {self.factory}")


@dataclass(frozen=True)
class WorldConfig:
    """World constructor and spawn settings."""

    kind: str = "flat"
    kwargs: dict[str, Any] = field(default_factory=dict)
    spawn_position: tuple[float, float, float] = (0.0, 0.0, 0.5)
    spawn_orientation: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)
    add_ground_contact_sensors: bool = False

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any] | None) -> "WorldConfig":
        values = dict(mapping or {})
        return cls(
            kind=str(values.pop("kind", values.pop("type", "flat"))).lower(),
            kwargs=dict(values.pop("kwargs", {}) or {}),
            spawn_position=tuple(values.pop("spawn_position", (0.0, 0.0, 0.5))),
            spawn_orientation=tuple(values.pop("spawn_orientation", (1.0, 0.0, 0.0, 0.0))),
            add_ground_contact_sensors=bool(values.pop("add_ground_contact_sensors", False)),
        )

    def validate(self) -> None:
        if self.kind not in {"flat", "blocks", "mixed"}:
            raise ValueError(f"Unsupported world kind: {self.kind}")
        if len(self.spawn_position) != 3 or len(self.spawn_orientation) != 4:
            raise ValueError("World spawn pose must contain 3 position and 4 quaternion values")


@dataclass(frozen=True)
class SimulationConfig:
    """Simulation construction settings."""

    timestep: float | None = 0.0001


@dataclass(frozen=True)
class RendererConfig:
    """Renderer settings passed to FlyGym ``Simulation.set_renderer``."""

    cameras: tuple[str, ...] = ("track",)
    camera_res: tuple[int, int] = (240, 320)
    playback_speed: float = 0.2
    output_fps: int = 25
    buffer_frames: bool = True
    kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FlyGymConfig:
    """Complete adapter configuration loaded from YAML or a mapping."""

    fly: FlyConfig = field(default_factory=FlyConfig)
    world: WorldConfig = field(default_factory=WorldConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    renderer: RendererConfig = field(default_factory=RendererConfig)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any] | None) -> "FlyGymConfig":
        values = dict(mapping or {})
        simulation_values = dict(values.get("simulation", {}) or {})
        renderer_values = dict(values.get("renderer", {}) or {})
        timestep_value = simulation_values.get("timestep", 0.0001)
        config = cls(
            fly=FlyConfig.from_mapping(values.get("fly")),
            world=WorldConfig.from_mapping(values.get("world")),
            simulation=SimulationConfig(
                timestep=None if timestep_value is None else float(timestep_value)
            ),
            renderer=RendererConfig(
                cameras=tuple(renderer_values.get("cameras", ("track",))),
                camera_res=tuple(renderer_values.get("camera_res", (240, 320))),
                playback_speed=float(renderer_values.get("playback_speed", 0.2)),
                output_fps=int(renderer_values.get("output_fps", 25)),
                buffer_frames=bool(renderer_values.get("buffer_frames", True)),
                kwargs=dict(renderer_values.get("kwargs", {}) or {}),
            ),
            metadata=dict(values.get("metadata", {}) or {}),
        )
        config.validate()
        return config

    @classmethod
    def from_yaml(cls, path: str | Path) -> "FlyGymConfig":
        with Path(path).open("r", encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle) or {}
        if not isinstance(loaded, dict):
            raise ValueError("FlyGym configuration root must be a mapping")
        return cls.from_mapping(loaded)

    def validate(self) -> None:
        self.fly.validate()
        self.world.validate()
        if self.simulation.timestep is not None and self.simulation.timestep <= 0:
            raise ValueError("simulation.timestep must be positive")
        if len(self.renderer.camera_res) != 2:
            raise ValueError("renderer.camera_res must contain height and width")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "fly": {
                "name": self.fly.name,
                "factory": self.fly.factory,
                "model_kwargs": self.fly.model_kwargs,
                "locomotion_kwargs": self.fly.locomotion_kwargs,
            },
            "world": {
                "kind": self.world.kind,
                "kwargs": self.world.kwargs,
                "spawn_position": list(self.world.spawn_position),
                "spawn_orientation": list(self.world.spawn_orientation),
                "add_ground_contact_sensors": self.world.add_ground_contact_sensors,
            },
            "simulation": {"timestep": self.simulation.timestep},
            "renderer": {
                "cameras": list(self.renderer.cameras),
                "camera_res": list(self.renderer.camera_res),
                "playback_speed": self.renderer.playback_speed,
                "output_fps": self.renderer.output_fps,
                "buffer_frames": self.renderer.buffer_frames,
                "kwargs": self.renderer.kwargs,
            },
            "metadata": self.metadata,
        }


__all__ = [
    "FlyConfig",
    "FlyGymConfig",
    "RendererConfig",
    "SimulationConfig",
    "WorldConfig",
]
