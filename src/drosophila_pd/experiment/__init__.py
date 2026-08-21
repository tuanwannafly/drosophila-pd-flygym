"""Real experiment orchestration and dataset management.

This package is intentionally integration-oriented. It does not provide a
default simulation implementation and therefore cannot fabricate a rollout.
"""

from .artifacts import ArtifactLayout, ArtifactManager, PublicationAssetManager
from .benchmark import BENCHMARK_OPERATIONS, ExperimentBenchmark
from .dataset import DATASET_ROLES, DATASET_SCOPE, DatasetManager, DatasetManifest, DatasetRecord, merge_dataset_managers
from .models import ARTIFACT_DIRECTORIES, ExperimentJob, ExperimentManifest, ExperimentResult, ExperimentStatus, SCIENTIFIC_SCOPE, STAGE_NAMES
from .runner import ExperimentLogger, ExperimentQueue, ExperimentRunner, ExperimentScheduler, StageHandler

__all__ = [
    "ARTIFACT_DIRECTORIES",
    "ArtifactLayout",
    "ArtifactManager",
    "BENCHMARK_OPERATIONS",
    "DATASET_ROLES",
    "DATASET_SCOPE",
    "DatasetManager",
    "DatasetManifest",
    "DatasetRecord",
    "ExperimentBenchmark",
    "ExperimentJob",
    "ExperimentLogger",
    "ExperimentManifest",
    "ExperimentQueue",
    "ExperimentResult",
    "ExperimentRunner",
    "ExperimentScheduler",
    "ExperimentStatus",
    "PublicationAssetManager",
    "SCIENTIFIC_SCOPE",
    "STAGE_NAMES",
    "StageHandler",
    "merge_dataset_managers",
]
