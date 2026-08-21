"""Deterministic campaign scheduling without execution."""

from __future__ import annotations

from .manager import CampaignManager
from .models import CampaignQueue, CampaignStatus


class CampaignScheduler:
    """Prepare and queue campaigns; dispatch only returns planned work."""

    def __init__(self, manager: CampaignManager) -> None:
        self.manager = manager
        self.queue = CampaignQueue()

    def prepare(self, campaign_id: str, *, dataset_available: bool) -> CampaignStatus:
        campaign = self.manager.set_dataset_available(campaign_id, dataset_available)
        return campaign.status

    def enqueue(self, campaign_id: str) -> str:
        campaign = self.manager.get(campaign_id)
        if campaign.status != CampaignStatus.READY:
            raise ValueError(f"campaign must be READY before queueing: {campaign.status.value}")
        self.queue.enqueue(campaign_id)
        self.queue.campaign_ids.sort(key=lambda item: (-self.manager.get(item).priority, item))
        self.manager.transition(campaign_id, CampaignStatus.QUEUED, reason="deterministic scheduler queue")
        return campaign_id

    def dispatch(self, *, limit: int | None = None) -> tuple[str, ...]:
        """Return queued campaign IDs without starting any experiment."""

        count = len(self.queue.campaign_ids) if limit is None else max(0, int(limit))
        return tuple(self.queue.campaign_ids[:count])

    def complete_dispatch(self, campaign_id: str) -> None:
        self.queue.remove(campaign_id)


__all__ = ["CampaignScheduler"]
