"""Synchronous, timer-free runtime orchestration for a FlyGym simulation."""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable

from .types import RolloutData


class RuntimeState(str, Enum):
    STOPPED = "Stopped"
    PAUSED = "Paused"
    RUNNING = "Running"


class FlyGymRuntime:
    """Control a supplied FlyGym ``Simulation`` without owning simulation policy."""

    def __init__(
        self,
        simulation: Any,
        *,
        recorder: Any | None = None,
        max_steps: int | None = None,
    ) -> None:
        self.simulation = simulation
        self.recorder = recorder
        self.max_steps = max_steps
        self.state = RuntimeState.STOPPED
        self._current_step = 0

    def _ensure_initial_recorded(self) -> None:
        if self.recorder is not None and not self.recorder.rollout.frames:
            self.recorder.record()

    @property
    def is_running(self) -> bool:
        return self.state is RuntimeState.RUNNING

    @property
    def current_step(self) -> int:
        return self._current_step

    @property
    def current_time(self) -> float:
        data = getattr(self.simulation, "mj_data", None)
        if data is not None and hasattr(data, "time"):
            return float(data.time)
        timestep = getattr(getattr(self.simulation, "mj_model", None), "opt", None)
        return float(self._current_step * getattr(timestep, "timestep", 0.0))

    def run(
        self,
        steps: int | None = None,
        *,
        on_step: Callable[["FlyGymRuntime"], None] | None = None,
    ) -> RolloutData | None:
        """Run synchronously for ``steps`` or configured ``max_steps``.

        No timer, scheduler, or playback loop is created. A callback may call
        ``pause`` or ``stop`` to end a controlled run.
        """

        target = self.max_steps if steps is None else steps
        if target is None or target < 0:
            raise ValueError("run() requires a non-negative steps value or max_steps")
        self._ensure_initial_recorded()
        self.state = RuntimeState.RUNNING
        completed = 0
        while self.state is RuntimeState.RUNNING and completed < target:
            self.step()
            completed += 1
            if on_step is not None:
                on_step(self)
        if self.state is RuntimeState.RUNNING:
            self.state = RuntimeState.STOPPED
        return self.recorder.rollout if self.recorder is not None else None

    def step(self) -> None:
        """Advance exactly one simulation step and capture one observation."""

        if self.state is RuntimeState.PAUSED:
            raise RuntimeError("Cannot step while runtime is paused; call resume()")
        if self.state is RuntimeState.STOPPED:
            self.state = RuntimeState.RUNNING
        self._ensure_initial_recorded()
        self.simulation.step()
        self._current_step += 1
        if self.recorder is not None:
            self.recorder.record()

    def reset(self) -> None:
        """Reset the supplied simulation and recorder to their initial state."""

        self.simulation.reset()
        self._current_step = 0
        self.state = RuntimeState.STOPPED
        if self.recorder is not None:
            self.recorder.reset()
            self.recorder.record()

    def pause(self) -> None:
        if self.state is RuntimeState.RUNNING:
            self.state = RuntimeState.PAUSED

    def resume(self) -> None:
        if self.state is RuntimeState.PAUSED:
            self.state = RuntimeState.RUNNING

    def stop(self) -> None:
        self.state = RuntimeState.STOPPED


__all__ = ["FlyGymRuntime", "RuntimeState"]
