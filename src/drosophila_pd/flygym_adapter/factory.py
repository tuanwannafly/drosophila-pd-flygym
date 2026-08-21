"""Lazy factories for the verified FlyGym 2.1.0 API surface."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from .config import FlyConfig, RendererConfig, SimulationConfig, WorldConfig
from .exceptions import FlyGymUnavailableError, UnsupportedFlyGymConfigurationError


def _import_flygym() -> Any:
    try:
        import flygym
    except ModuleNotFoundError as exc:
        raise FlyGymUnavailableError(
            "FlyGym is not installed. Install the pinned simulation extra in a "
            "Python 3.12 environment before creating live objects."
        ) from exc
    return flygym


def create_fly(config: FlyConfig | Mapping[str, Any] | None = None, **overrides: Any) -> Any:
    """Create a FlyGym fly through the selected verified factory."""

    fly_config = config if isinstance(config, FlyConfig) else FlyConfig.from_mapping(config)
    if overrides:
        fly_config = FlyConfig(
            name=str(overrides.pop("name", fly_config.name)),
            factory=str(overrides.pop("factory", fly_config.factory)),
            model_kwargs={**fly_config.model_kwargs, **overrides},
            locomotion_kwargs=fly_config.locomotion_kwargs,
        )
    fly_config.validate()
    _import_flygym()

    if fly_config.factory == "canonical_locomotion":
        try:
            from flygym_demo.complex_terrain import make_locomotion_fly
        except ModuleNotFoundError as exc:
            raise FlyGymUnavailableError(
                "The repository's canonical locomotion helper "
                "flygym_demo.complex_terrain is unavailable in this environment."
            ) from exc
        kwargs = dict(fly_config.locomotion_kwargs)
        kwargs.update(fly_config.model_kwargs)
        return make_locomotion_fly(name=fly_config.name, **kwargs)

    from flygym.compose import NeuroMechFly

    return NeuroMechFly(name=fly_config.name, **fly_config.model_kwargs)


def create_world(config: WorldConfig | Mapping[str, Any] | None = None) -> Any:
    """Create a FlatGroundWorld, BlocksTerrainWorld, or MixedTerrainWorld."""

    world_config = config if isinstance(config, WorldConfig) else WorldConfig.from_mapping(config)
    world_config.validate()
    _import_flygym()
    from flygym.compose import BlocksTerrainWorld, FlatGroundWorld, MixedTerrainWorld

    constructors = {
        "flat": FlatGroundWorld,
        "blocks": BlocksTerrainWorld,
        "mixed": MixedTerrainWorld,
    }
    return constructors[world_config.kind](**world_config.kwargs)


def attach_fly(
    world: Any,
    fly: Any,
    *,
    position: tuple[float, float, float] | list[float] | np.ndarray = (0.0, 0.0, 0.5),
    orientation: tuple[float, float, float, float] | list[float] | np.ndarray = (1.0, 0.0, 0.0, 0.0),
    **kwargs: Any,
) -> Any:
    """Attach a fly through FlyGym's public ``BaseWorld.add_fly`` API."""

    _import_flygym()
    from flygym.utils.math import Rotation3D

    world.add_fly(
        fly,
        spawn_position=np.asarray(position, dtype=float),
        spawn_rotation=Rotation3D("quat", np.asarray(orientation, dtype=float).tolist()),
        **kwargs,
    )
    return world


def create_simulation(world: Any, config: SimulationConfig | Mapping[str, Any] | None = None) -> Any:
    """Create FlyGym's CPU ``Simulation`` for an already configured world."""

    simulation_config = config if isinstance(config, SimulationConfig) else SimulationConfig(**dict(config or {}))
    _import_flygym()
    from flygym import Simulation

    return Simulation(world, timestep=simulation_config.timestep)


def create_renderer(
    simulation: Any,
    config: RendererConfig | Mapping[str, Any] | None = None,
    *,
    cameras: str | list[str] | None = None,
    **overrides: Any,
) -> Any:
    """Attach FlyGym's Renderer through ``Simulation.set_renderer``."""

    renderer_config = config if isinstance(config, RendererConfig) else RendererConfig(**dict(config or {}))
    camera_spec: str | list[str] = cameras or list(renderer_config.cameras)
    kwargs = dict(renderer_config.kwargs)
    kwargs.update(overrides)
    if not hasattr(simulation, "set_renderer"):
        raise UnsupportedFlyGymConfigurationError(
            "The supplied object does not expose FlyGym Simulation.set_renderer."
        )
    return simulation.set_renderer(
        camera_spec,
        camera_res=renderer_config.camera_res,
        playback_speed=renderer_config.playback_speed,
        output_fps=renderer_config.output_fps,
        buffer_frames=renderer_config.buffer_frames,
        **kwargs,
    )


__all__ = ["attach_fly", "create_fly", "create_renderer", "create_simulation", "create_world"]
