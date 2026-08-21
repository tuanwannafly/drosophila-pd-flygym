"""Large-scale campaign planning and tracking APIs.

Project Y is orchestration infrastructure only. It does not execute FlyGym,
create rollout data, or make biological claims.
"""

from .logger import CampaignLogger
from .manager import CampaignManager, TRANSITIONS
from .models import (
    CAMPAIGN_SCOPE,
    Campaign,
    CampaignHistory,
    CampaignManifest,
    CampaignProgress,
    CampaignQueue,
    CampaignStatus,
    CampaignSummary,
    current_provenance,
)
from .scheduler import CampaignScheduler

__all__ = [
    "CAMPAIGN_SCOPE",
    "Campaign",
    "CampaignHistory",
    "CampaignLogger",
    "CampaignManager",
    "CampaignManifest",
    "CampaignProgress",
    "CampaignQueue",
    "CampaignScheduler",
    "CampaignStatus",
    "CampaignSummary",
    "TRANSITIONS",
    "current_provenance",
]
