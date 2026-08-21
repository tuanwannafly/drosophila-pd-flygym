"""Read-only adapter for curated FlyGym rollout datasets."""

from .dataset_metadata import DatasetMetadata
from .dataset_validator import DatasetValidationReport, DatasetValidator
from .flygym_dataset import DATASET_TYPES, DatasetDiscoveryReport, FlyGymDataset, discover_datasets
from .manifest_builder import ManifestBuilder
from .rollout_locator import RolloutFile, RolloutLocator

__all__ = [
    "DATASET_TYPES",
    "DatasetDiscoveryReport",
    "DatasetMetadata",
    "DatasetValidationReport",
    "DatasetValidator",
    "FlyGymDataset",
    "ManifestBuilder",
    "RolloutFile",
    "RolloutLocator",
    "discover_datasets",
]
