"""Autonomous research campaign orchestration over existing artifacts.

The package provides lifecycle, scheduling, provenance, validation, and
reporting primitives. It does not execute FlyGym/MuJoCo or create rollout data.
"""

from .campaign import CAMPAIGN_SCOPE, Campaign, ExperimentSpec
from .campaign_events import CampaignEvent
from .campaign_history import CampaignHistory
from .campaign_manager import CampaignManager
from .campaign_manifest import CampaignManifest, build_manifest
from .campaign_state import CampaignState, TERMINAL_STATES, coerce_state

__all__ = [
    "CAMPAIGN_SCOPE",
    "Campaign",
    "CampaignEvent",
    "CampaignHistory",
    "CampaignManager",
    "CampaignManifest",
    "CampaignState",
    "ExperimentSpec",
    "TERMINAL_STATES",
    "build_manifest",
    "coerce_state",
]
