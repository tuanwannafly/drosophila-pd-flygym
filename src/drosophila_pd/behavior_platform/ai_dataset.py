"""Dataset containers, manifests, checksums, and IO for v2 AI analysis."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


AI_PLATFORM_SCOPE = (
    "AI-assisted computational behavior analysis only. Synthetic examples and "
    "model outputs are not biological evidence or Parkinson's disease "
    "validation."
)


@dataclass(frozen=True)
class BehaviorSample:
    """One behavior sample with arrays, labels, and metadata."""

    sample_id: str
    condition: str
    arrays: Mapping[str, Any]
    labels: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "condition": self.condition,
            "arrays": {name: _array_to_list(value) for name, value in self.arrays.items()},
            "labels": list(self.labels),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BehaviorSample":
        return cls(
            sample_id=str(data["sample_id"]),
            condition=str(data["condition"]),
            arrays=dict(data.get("arrays", {})),
            labels=tuple(data.get("labels", ())),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class BehaviorDataset:
    """Versioned collection of behavior samples."""

    dataset_id: str
    version: str
    samples: tuple[BehaviorSample, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "scientific_scope": AI_PLATFORM_SCOPE,
            "sample_count": len(self.samples),
            "samples": [sample.as_dict() for sample in self.samples],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BehaviorDataset":
        return cls(
            dataset_id=str(data["dataset_id"]),
            version=str(data["version"]),
            samples=tuple(BehaviorSample.from_dict(item) for item in data.get("samples", ())),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass(frozen=True)
class BehaviorSequenceDataset:
    """Dataset wrapper for ordered behavior sequences."""

    dataset: BehaviorDataset
    sequence_order: tuple[str, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset": self.dataset.as_dict(),
            "sequence_order": list(self.sequence_order),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class BehaviorIndex:
    """Search index over dataset samples."""

    sample_ids: tuple[str, ...]
    conditions: Mapping[str, tuple[str, ...]]
    labels: Mapping[str, tuple[str, ...]]

    def as_dict(self) -> dict[str, Any]:
        return {
            "sample_ids": list(self.sample_ids),
            "conditions": {key: list(value) for key, value in self.conditions.items()},
            "labels": {key: list(value) for key, value in self.labels.items()},
        }


@dataclass(frozen=True)
class DatasetManifest:
    """Versioned dataset manifest with checksums."""

    dataset_id: str
    version: str
    sample_count: int
    checksums: Mapping[str, str]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "sample_count": int(self.sample_count),
            "checksums": dict(self.checksums),
            "metadata": dict(self.metadata),
        }


def build_behavior_index(dataset: BehaviorDataset) -> BehaviorIndex:
    """Build condition and label lookup tables for a dataset."""

    conditions: dict[str, list[str]] = {}
    labels: dict[str, list[str]] = {}
    for sample in dataset.samples:
        conditions.setdefault(sample.condition, []).append(sample.sample_id)
        for label in sample.labels:
            labels.setdefault(label, []).append(sample.sample_id)
    return BehaviorIndex(
        sample_ids=tuple(sample.sample_id for sample in dataset.samples),
        conditions={key: tuple(value) for key, value in conditions.items()},
        labels={key: tuple(value) for key, value in labels.items()},
    )


def create_dataset_manifest(dataset: BehaviorDataset) -> DatasetManifest:
    """Create a checksum manifest from sample payloads."""

    checksums = {
        sample.sample_id: hashlib.sha256(
            json.dumps(sample.as_dict(), sort_keys=True).encode("utf-8")
        ).hexdigest()
        for sample in dataset.samples
    }
    return DatasetManifest(
        dataset_id=dataset.dataset_id,
        version=dataset.version,
        sample_count=len(dataset.samples),
        checksums=checksums,
        metadata={"scientific_scope": AI_PLATFORM_SCOPE},
    )


class DatasetExporter:
    """Export datasets to JSON, CSV, NPZ, Parquet, or Arrow."""

    @staticmethod
    def export(dataset: BehaviorDataset, output_path: str | Path, *, format: str | None = None) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fmt = (format or path.suffix.lstrip(".")).lower()
        if fmt == "json":
            path.write_text(json.dumps(dataset.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
        elif fmt == "csv":
            _write_dataset_csv(dataset, path)
        elif fmt == "npz":
            _write_dataset_npz(dataset, path)
        elif fmt in {"parquet", "arrow"}:
            _write_optional_columnar(dataset, path, fmt)
        else:
            raise ValueError(f"unsupported dataset export format: {fmt}")
        return path


class DatasetLoader:
    """Load datasets from supported formats."""

    @staticmethod
    def load(path: str | Path, *, format: str | None = None) -> BehaviorDataset:
        source = Path(path)
        fmt = (format or source.suffix.lstrip(".")).lower()
        if fmt == "json":
            return BehaviorDataset.from_dict(json.loads(source.read_text(encoding="utf-8")))
        if fmt == "csv":
            return _read_dataset_csv(source)
        if fmt == "npz":
            return _read_dataset_npz(source)
        if fmt in {"parquet", "arrow"}:
            return _read_optional_columnar(source, fmt)
        raise ValueError(f"unsupported dataset load format: {fmt}")


def verify_dataset_integrity(dataset: BehaviorDataset, manifest: DatasetManifest) -> bool:
    """Verify dataset sample checksums against a manifest."""

    current = create_dataset_manifest(dataset)
    return (
        current.dataset_id == manifest.dataset_id
        and current.version == manifest.version
        and current.sample_count == manifest.sample_count
        and dict(current.checksums) == dict(manifest.checksums)
    )


def _write_dataset_csv(dataset: BehaviorDataset, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["sample_id", "condition", "labels", "metadata", "arrays"])
        writer.writeheader()
        for sample in dataset.samples:
            writer.writerow(
                {
                    "sample_id": sample.sample_id,
                    "condition": sample.condition,
                    "labels": "|".join(sample.labels),
                    "metadata": json.dumps(dict(sample.metadata), sort_keys=True),
                    "arrays": json.dumps({k: _array_to_list(v) for k, v in sample.arrays.items()}, sort_keys=True),
                }
            )


def _read_dataset_csv(path: Path) -> BehaviorDataset:
    samples = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            samples.append(
                BehaviorSample(
                    sample_id=row["sample_id"],
                    condition=row["condition"],
                    labels=tuple(filter(None, row.get("labels", "").split("|"))),
                    metadata=json.loads(row.get("metadata") or "{}"),
                    arrays=json.loads(row.get("arrays") or "{}"),
                )
            )
    return BehaviorDataset(dataset_id=path.stem, version="loaded_csv", samples=tuple(samples))


def _write_dataset_npz(dataset: BehaviorDataset, path: Path) -> None:
    arrays: dict[str, np.ndarray] = {
        "manifest_json": np.asarray(json.dumps(dataset.as_dict(), sort_keys=True)),
    }
    for sample in dataset.samples:
        for name, value in sample.arrays.items():
            arrays[f"{sample.sample_id}__{name}"] = np.asarray(value, dtype=float)
    np.savez_compressed(path, **arrays)


def _read_dataset_npz(path: Path) -> BehaviorDataset:
    data = np.load(path, allow_pickle=False)
    manifest = json.loads(str(data["manifest_json"]))
    return BehaviorDataset.from_dict(manifest)


def _write_optional_columnar(dataset: BehaviorDataset, path: Path, fmt: str) -> None:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"pyarrow is required for {fmt} dataset export.") from exc
    rows = [
        {
            "sample_id": sample.sample_id,
            "condition": sample.condition,
            "labels": list(sample.labels),
            "metadata_json": json.dumps(dict(sample.metadata), sort_keys=True),
            "arrays_json": json.dumps({k: _array_to_list(v) for k, v in sample.arrays.items()}, sort_keys=True),
        }
        for sample in dataset.samples
    ]
    table = pa.Table.from_pylist(rows)
    if fmt == "parquet":
        pq.write_table(table, path)
    else:
        with path.open("wb") as handle:
            with pa.ipc.new_file(handle, table.schema) as writer:
                writer.write(table)


def _read_optional_columnar(path: Path, fmt: str) -> BehaviorDataset:
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(f"pyarrow is required for {fmt} dataset loading.") from exc
    table = pq.read_table(path) if fmt == "parquet" else pa.ipc.open_file(path.open("rb")).read_all()
    samples = []
    for row in table.to_pylist():
        samples.append(
            BehaviorSample(
                sample_id=row["sample_id"],
                condition=row["condition"],
                labels=tuple(row.get("labels") or ()),
                metadata=json.loads(row.get("metadata_json") or "{}"),
                arrays=json.loads(row.get("arrays_json") or "{}"),
            )
        )
    return BehaviorDataset(dataset_id=path.stem, version=f"loaded_{fmt}", samples=tuple(samples))


def _array_to_list(value: Any) -> Any:
    array = np.asarray(value)
    return array.tolist() if array.ndim else array.item()


__all__ = [
    "AI_PLATFORM_SCOPE",
    "BehaviorDataset",
    "BehaviorIndex",
    "BehaviorSample",
    "BehaviorSequenceDataset",
    "DatasetExporter",
    "DatasetLoader",
    "DatasetManifest",
    "build_behavior_index",
    "create_dataset_manifest",
    "verify_dataset_integrity",
]
