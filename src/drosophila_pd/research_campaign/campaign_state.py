"""Lifecycle state types for research campaign orchestration."""

from __future__ import annotations

from enum import Enum


class CampaignState(str, Enum):
    """State of a campaign or scheduled experiment."""

    QUEUED = "QUEUED"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    RETRY = "RETRY"


TERMINAL_STATES = frozenset({CampaignState.CANCELLED, CampaignState.COMPLETED})


def coerce_state(value: CampaignState | str) -> CampaignState:
    """Convert a serialized state to :class:`CampaignState`."""

    return value if isinstance(value, CampaignState) else CampaignState(str(value).upper())


__all__ = ["CampaignState", "TERMINAL_STATES", "coerce_state"]
