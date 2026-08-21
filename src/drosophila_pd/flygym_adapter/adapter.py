"""Public facade for FlyGym construction and runtime integration."""

from __future__ import annotations

from typing import Any, Mapping

from .config import FlyConfig, RendererConfig, SimulationConfig, WorldConfig
from .factory import attach_fly, create_fly, create_renderer, create_simulation, create_world


class FlyGymAdapter:
    """The project-facing facade for FlyGym 2.1.0 objects."""

    def create_fly(self, config: FlyConfig | Mapping[str, Any] | None = None, **kwargs: Any) -> Any:
        return create_fly(config, **kwargs)

    def create_world(self, config: WorldConfig | Mapping[str, Any] | None = None) -> Any:
        return create_world(config)

    def attach_fly(self, world: Any, fly: Any, **kwargs: Any) -> Any:
        return attach_fly(world, fly, **kwargs)

    def create_simulation(
        self,
        world: Any,
        config: SimulationConfig | Mapping[str, Any] | None = None,
    ) -> Any:
        return create_simulation(world, config)

    def create_renderer(
        self,
        simulation: Any,
        config: RendererConfig | Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        return create_renderer(simulation, config, **kwargs)


__all__ = ["FlyGymAdapter"]
