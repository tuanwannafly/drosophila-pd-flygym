"""Small builders over the FlyGym adapter factories."""

from __future__ import annotations

from typing import Any

from .config import FlyConfig, SimulationConfig, WorldConfig
from .factory import attach_fly, create_fly, create_simulation, create_world


class FlyBuilder:
    """Build a configured FlyGym fly without exposing FlyGym imports to callers."""

    def __init__(self) -> None:
        self._config = FlyConfig()
        self._position = (0.0, 0.0, 0.5)
        self._orientation = (1.0, 0.0, 0.0, 0.0)
        self._pose: Any = None

    def healthy(self) -> "FlyBuilder":
        self._config = FlyConfig()
        return self

    def position(self, value: tuple[float, float, float] | list[float]) -> "FlyBuilder":
        self._position = tuple(float(item) for item in value)
        return self

    def orientation(self, value: tuple[float, float, float, float] | list[float]) -> "FlyBuilder":
        self._orientation = tuple(float(item) for item in value)
        return self

    def pose(self, value: Any) -> "FlyBuilder":
        self._pose = value
        if isinstance(value, dict):
            if "position" in value:
                self.position(value["position"])
            if "orientation" in value:
                self.orientation(value["orientation"])
        return self

    @property
    def spawn_position(self) -> tuple[float, float, float]:
        return self._position

    @property
    def spawn_orientation(self) -> tuple[float, float, float, float]:
        return self._orientation

    def build(self) -> Any:
        return create_fly(self._config)


class WorldBuilder:
    """Build a supported world and optionally attach one or more fly objects."""

    def __init__(self) -> None:
        self._config = WorldConfig()
        self._flies: list[tuple[Any, tuple[float, float, float], tuple[float, float, float, float], dict[str, Any]]] = []

    def flat(self, **kwargs: Any) -> "WorldBuilder":
        self._config = WorldConfig(kind="flat", kwargs=kwargs)
        return self

    def blocks(self, **kwargs: Any) -> "WorldBuilder":
        self._config = WorldConfig(kind="blocks", kwargs=kwargs)
        return self

    def mixed(self, **kwargs: Any) -> "WorldBuilder":
        self._config = WorldConfig(kind="mixed", kwargs=kwargs)
        return self

    def with_fly(
        self,
        fly: Any,
        *,
        position: tuple[float, float, float] = (0.0, 0.0, 0.5),
        orientation: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0),
        **kwargs: Any,
    ) -> "WorldBuilder":
        self._flies.append((fly, position, orientation, kwargs))
        return self

    def build(self) -> Any:
        world = create_world(self._config)
        for fly, position, orientation, kwargs in self._flies:
            attach_fly(world, fly, position=position, orientation=orientation, **kwargs)
        return world


class SimulationBuilder:
    """Build a FlyGym Simulation from an already configured world."""

    def __init__(self) -> None:
        self._world: Any = None
        self._config = SimulationConfig()

    def with_world(self, world: Any) -> "SimulationBuilder":
        self._world = world
        return self

    def timestep(self, value: float | None) -> "SimulationBuilder":
        self._config = SimulationConfig(timestep=value)
        return self

    def build(self) -> Any:
        if self._world is None:
            raise ValueError("SimulationBuilder requires with_world(...) before build()")
        return create_simulation(self._world, self._config)


__all__ = ["FlyBuilder", "SimulationBuilder", "WorldBuilder"]
