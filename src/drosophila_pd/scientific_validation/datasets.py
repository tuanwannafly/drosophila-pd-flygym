"""Reference dataset registration and integrity checks.

The manager indexes files or already-imported :class:`RolloutData` objects. It
never creates observations and never runs a simulator.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData


REFERENCE_ROLES = (
    "Healthy",
    "PD",
    "Candidate",
    "Control",
    "Validation Set",
    "Benchmark Set",
)


@dataclass(frozen=True)
class ReferenceDataset:
    """A named collection of real imported data references."""

    dataset_id: str
    role: str
    entries: Mapping[str, str | Path | RolloutData]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.dataset_id.strip():
            raise ValueError("dataset_id must not be empty")
        if self.role not in REFERENCE_ROLES:
            raise ValueError(f"role must be one of {REFERENCE_ROLES}")
        if not self.entries:
            raise ValueError("entries must contain at least one imported reference")

    def load(self, *, base_dir: str | Path | None = None) -> dict[str, RolloutData]:
        """Load registered JSON/NPZ rollout entries without altering them."""

        root = Path(base_dir) if base_dir is not None else Path.cwd()
        loaded: dict[str, RolloutData] = {}
        for entry_id, entry in self.entries.items():
            if isinstance(entry, RolloutData):
                loaded[str(entry_id)] = entry
                continue
            path = Path(entry)
            if not path.is_absolute():
                path = root / path
            loaded[str(entry_id)] = _load_rollout(path)
        return loaded

    def validate_paths(self, *, base_dir: str | Path | None = None) -> dict[str, Any]:
        root = Path(base_dir) if base_dir is not None else Path.cwd()
        checks: dict[str, bool] = {}
        for entry_id, entry in self.entries.items():
            checks[str(entry_id)] = isinstance(entry, RolloutData) or _resolve(root, entry).is_file()
        return {"dataset_id": self.dataset_id, "role": self.role, "checks": checks, "overall_pass": all(checks.values())}

    def manifest_record(self, *, base_dir: str | Path | None = None) -> dict[str, Any]:
        root = Path(base_dir) if base_dir is not None else Path.cwd()
        entries = []
        for entry_id, entry in self.entries.items():
            if isinstance(entry, RolloutData):
                entries.append({"entry_id": str(entry_id), "in_memory": True, "condition_id": entry.condition_id})
            else:
                path = _resolve(root, entry)
                entries.append({"entry_id": str(entry_id), "path": str(path), "exists": path.is_file(), "sha256": _sha256(path) if path.is_file() else None})
        return {"dataset_id": self.dataset_id, "role": self.role, "metadata": dict(self.metadata), "entries": entries}


class ReferenceDatasetManager:
    """Registry for Healthy/Candidate/validation references."""

    def __init__(self, datasets: Mapping[str, ReferenceDataset] | None = None) -> None:
        self._datasets = dict(datasets or {})

    def register(self, dataset: ReferenceDataset) -> None:
        if dataset.dataset_id in self._datasets:
            raise ValueError(f"dataset already registered: {dataset.dataset_id}")
        self._datasets[dataset.dataset_id] = dataset

    def get(self, dataset_id: str) -> ReferenceDataset:
        try:
            return self._datasets[dataset_id]
        except KeyError as exc:
            raise KeyError(f"unknown reference dataset: {dataset_id}") from exc

    def datasets(self) -> tuple[ReferenceDataset, ...]:
        return tuple(self._datasets.values())

    def validate(self, *, base_dir: str | Path | None = None) -> dict[str, Any]:
        results = [dataset.validate_paths(base_dir=base_dir) for dataset in self.datasets()]
        return {"dataset_count": len(results), "datasets": results, "overall_pass": bool(results) and all(item["overall_pass"] for item in results)}

    def manifest(self, *, base_dir: str | Path | None = None) -> dict[str, Any]:
        return {"manager_version": 1, "datasets": [dataset.manifest_record(base_dir=base_dir) for dataset in self.datasets()]}

    @classmethod
    def from_manifest(cls, path: str | Path) -> "ReferenceDatasetManager":
        manifest_path = Path(path)
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        datasets: dict[str, ReferenceDataset] = {}
        for record in payload.get("datasets", []):
            entries = {}
            for entry in record.get("rollouts", record.get("entries", [])):
                if "path" not in entry:
                    raise ValueError("manifest entries must point to imported files")
                entry_path = Path(entry["path"])
                entries[str(entry["entry_id"])] = str(
                    entry_path if entry_path.is_absolute() else manifest_path.parent / entry_path
                )
            dataset = ReferenceDataset(
                dataset_id=str(record["dataset_id"]),
                role=str(record["role"]),
                entries=entries,
                metadata=record.get("metadata", {}),
            )
            datasets[dataset.dataset_id] = dataset
        return cls(datasets)


def _load_rollout(path: Path) -> RolloutData:
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".npz":
        with np.load(path, allow_pickle=False) as archive:
            payload = {key: archive[key].tolist() for key in archive.files}
    elif path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"unsupported rollout reference format: {path.suffix}")
    return RolloutData.from_mapping(payload)


def _resolve(root: Path, entry: str | Path | RolloutData) -> Path:
    path = Path(entry)
    return path if path.is_absolute() else root / path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["REFERENCE_ROLES", "ReferenceDataset", "ReferenceDatasetManager"]
