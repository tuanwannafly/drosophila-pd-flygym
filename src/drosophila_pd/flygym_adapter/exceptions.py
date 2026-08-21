"""Exceptions raised by the FlyGym integration boundary."""

from __future__ import annotations


class FlyGymAdapterError(RuntimeError):
    """Base class for adapter and runtime errors."""


class FlyGymUnavailableError(FlyGymAdapterError):
    """Raised when the requested FlyGym runtime is not installed."""


class UnsupportedFlyGymConfigurationError(FlyGymAdapterError):
    """Raised when a configuration is outside the verified adapter surface."""


class RolloutExportError(FlyGymAdapterError):
    """Raised when a recorded rollout cannot be exported."""


__all__ = [
    "FlyGymAdapterError",
    "FlyGymUnavailableError",
    "RolloutExportError",
    "UnsupportedFlyGymConfigurationError",
]
