"""Real dataset acquisition, registry, and health-reporting APIs.

This package accepts caller-supplied files only. It never runs simulation,
creates rollout data, or interprets a dataset biologically.
"""

from .index import DatasetIndex
from .models import (
    DATASET_BUCKETS,
    DATASET_CATEGORIES,
    DATASET_SCOPE,
    DatasetChecksum,
    DatasetEntry,
    DatasetManifest,
    DatasetMetadata,
    DatasetVersion,
)
from .registry import DatasetImportResult, DatasetRegistry
from .scanner import DatasetScanner
from .validator import DatasetHealthReport, DatasetValidator

__all__ = [
    "DATASET_BUCKETS",
    "DATASET_CATEGORIES",
    "DATASET_SCOPE",
    "DatasetChecksum",
    "DatasetEntry",
    "DatasetHealthReport",
    "DatasetImportResult",
    "DatasetIndex",
    "DatasetManifest",
    "DatasetMetadata",
    "DatasetRegistry",
    "DatasetScanner",
    "DatasetValidator",
    "DatasetVersion",
]
