"""Execution-only orchestration for prepared research campaigns.

This package discovers supplied dataset manifests and delegates ready work to
the existing research pipeline. It never creates rollout data or runs a
simulation itself.
"""

from .artifact_registry import ARTIFACT_CATEGORIES, ArtifactRecord, ArtifactRegistry
from .execution_context import ExecutionContext
from .execution_history import ExecutionEvent, ExecutionHistory
from .execution_result import ExecutionResult
from .execution_runtime import DatasetDiscovery, DatasetRecord, DiscoveryReport, ExecutionRuntime
from .execution_state import ExecutionState, coerce_state
from .automation import (
    AutomationRunner,
    CampaignPlan,
    ExecutionJob,
    ExecutionQueue,
    ResearchAutomation,
    load_campaign_plan,
)

__all__ = [
    "ARTIFACT_CATEGORIES",
    "ArtifactRecord",
    "ArtifactRegistry",
    "DatasetDiscovery",
    "DatasetRecord",
    "DiscoveryReport",
    "ExecutionContext",
    "ExecutionEvent",
    "ExecutionHistory",
    "ExecutionResult",
    "ExecutionRuntime",
    "ExecutionState",
    "AutomationRunner",
    "CampaignPlan",
    "ExecutionJob",
    "ExecutionQueue",
    "ResearchAutomation",
    "coerce_state",
    "load_campaign_plan",
]
