"""Dataset objects and discovery for real, curated FlyGym outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from .dataset_metadata import DatasetMetadata
from .rollout_locator import RolloutFile, RolloutLocator


DATASET_TYPES = ("healthy", "pd", "candidate", "control", "validation", "benchmark")
MANIFEST_NAMES = ("manifest.json", "manifest.yaml", "manifest.yml", "dataset_manifest.json", "dataset_manifest.yaml", "dataset_manifest.yml")


@dataclass
class FlyGymDataset:
    """A manifest-backed, read-only FlyGym dataset."""

    dataset_id: str
    dataset_type: str
    dataset_version: str
    root: Path
    manifest_path: Path
    manifest: Mapping[str, Any]
    metadata: DatasetMetadata
    rollout_files: tuple[RolloutFile, ...]
    status: str = "READY"
    warnings: list[str] = field(default_factory=list)

    @property
    def trajectory_files(self) -> tuple[RolloutFile, ...]:
        return tuple(item for item in self.rollout_files if item.kind == "trajectory")

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_type": self.dataset_type,
            "dataset_version": self.dataset_version,
            "root": self.root.as_posix(),
            "manifest": self.manifest_path.as_posix(),
            "status": self.status,
            "metadata": self.metadata.as_dict(),
            "rollouts": [item.as_dict() for item in self.rollout_files],
            "trajectory_file_count": len(self.trajectory_files),
            "warnings": list(self.warnings),
        }

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "FlyGymDataset":
        path = Path(manifest_path).resolve()
        root = path.parent
        manifest = _read_structured(path)
        locator = RolloutLocator()
        rollout_files = locator.locate(root, manifest)
        metadata = DatasetMetadata.load(root, manifest)
        warnings = []
        if not manifest:
            warnings.append("manifest could not be parsed")
        return cls(
            dataset_id=str(manifest.get("dataset_id", root.name)),
            dataset_type=str(manifest.get("dataset_type", "unknown")),
            dataset_version=str(manifest.get("dataset_version", "")),
            root=root,
            manifest_path=path,
            manifest=manifest,
            metadata=metadata,
            rollout_files=rollout_files,
            warnings=warnings,
        )


@dataclass
class DatasetDiscoveryReport:
    """All dataset categories found or missing under configured roots."""

    state: str
    datasets: list[FlyGymDataset]
    missing_types: list[str]
    searched_roots: tuple[Path, ...]
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "datasets": [dataset.as_dict() for dataset in self.datasets],
            "missing_types": list(self.missing_types),
            "searched_roots": [path.as_posix() for path in self.searched_roots],
            "warnings": list(self.warnings),
            "rollout_parsing": "read-only validation only",
        }


def discover_datasets(
    roots: Sequence[str | Path],
    *,
    dataset_types: Sequence[str] = DATASET_TYPES,
) -> DatasetDiscoveryReport:
    """Find manifest-backed dataset directories without creating any files."""

    searched = tuple(Path(root).resolve() for root in roots)
    datasets: list[FlyGymDataset] = []
    missing: list[str] = []
    warnings: list[str] = []
    for dataset_type in dataset_types:
        matches: list[Path] = []
        for root in searched:
            typed_root = root / dataset_type
            if typed_root.is_dir():
                matches.extend(path for path in typed_root.rglob("*") if path.is_file() and path.name in MANIFEST_NAMES)
        if not matches:
            missing.append(dataset_type)
            continue
        for manifest_path in sorted(set(matches)):
            dataset = FlyGymDataset.from_manifest(manifest_path)
            datasets.append(dataset)
    if not datasets:
        warnings.append("No FlyGym dataset manifest was found.")
    state = "READY" if datasets else "WAITING_DATASET"
    return DatasetDiscoveryReport(state, datasets, missing, searched, warnings)


def _read_structured(path: Path) -> dict[str, Any]:
    try:
        if path.suffix.casefold() == ".json":
            import json

            value = json.loads(path.read_text(encoding="utf-8"))
        else:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:  # external manifest errors become validation findings
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["DATASET_TYPES", "DatasetDiscoveryReport", "FlyGymDataset", "discover_datasets"]
