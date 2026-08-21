"""Lifecycle states for the orchestration kernel."""

from __future__ import annotations

from enum import StrEnum


class KernelState(StrEnum):
    """States exposed by :class:`ResearchKernel`."""

    STOPPED = "STOPPED"
    BOOTING = "BOOTING"
    READY = "READY"
    WAITING_DATASET = "WAITING_DATASET"
    RUNNING = "RUNNING"
    SHUTDOWN = "SHUTDOWN"
    FAILED = "FAILED"


__all__ = ["KernelState"]
