"""Manifest-first management of real experiment dataset files."""

from __future__ import annotations

import hashlib
import json
import random
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.campaign_provenance import file_sha256, stable_hash


DATASET_ROLES = ("healthy", "pd", "candidate", "benchmark", "validation", "metadata")
DATASET_SCOPE = "Managed computational data files only; no fabricated scientific data or biological claim."


@dataclass(frozen=True)
class DatasetRecord:
    """One existing file registered in the dataset manifest."""

    record_id: str
    role: str
    path: str
    sha256: str
    byte_size: int
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "role": self.role,
            "path": self.path,
            "sha256": self.sha256,
            "byte_size": int(self.byte_size),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class DatasetManifest:
    """Versioned manifest for registered files."""

    dataset_id: str
    version: str
    records: tuple[DatasetRecord, ...]
    configuration_hash: str
    scientific_scope: str = DATASET_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": 1,
            "dataset_id": self.dataset_id,
            "version": self.version,
            "records": [record.as_dict() for record in self.records],
            "record_count": len(self.records),
            "configuration_hash": self.configuration_hash,
            "scientific_scope": self.scientific_scope,
        }


class DatasetManager:
    """Create and verify a dataset layout without creating sample data."""

    def __init__(self, root: str | Path, *, dataset_id: str = "dataset", version: str = "v2.dataset.1") -> None:
        self.root = Path(root)
        self.dataset_id = dataset_id
        self.version = version
        self._records: dict[str, DatasetRecord] = {}

    def initialize(self) -> Path:
        for role in DATASET_ROLES:
            (self.root / role).mkdir(parents=True, exist_ok=True)
        self._write_files()
        return self.root

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    @property
    def checksum_path(self) -> Path:
        return self.root / "checksum.json"

    def register_file(
        self,
        path: str | Path,
        role: str,
        *,
        record_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        copy: bool = False,
    ) -> DatasetRecord:
        if role not in DATASET_ROLES:
            raise ValueError(f"unsupported dataset role: {role}")
        source = Path(path)
        if not source.is_file():
            raise FileNotFoundError(source)
        self.initialize()
        target = source
        if copy:
            target = self.root / role / source.name
            if source.resolve() != target.resolve():
                shutil.copy2(source, target)
        identifier = record_id or source.stem
        if identifier in self._records:
            raise ValueError(f"duplicate record_id: {identifier}")
        digest = file_sha256(target)
        if any(record.sha256 == digest for record in self._records.values()):
            raise ValueError(f"duplicate file content for record_id: {identifier}")
        record = DatasetRecord(
            record_id=identifier,
            role=role,
            path=self._relative_or_absolute(target),
            sha256=digest,
            byte_size=target.stat().st_size,
            metadata=dict(metadata or {}),
        )
        self._records[identifier] = record
        self._write_files()
        return record

    def records(self) -> tuple[DatasetRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def manifest(self) -> DatasetManifest:
        payload = {
            "dataset_id": self.dataset_id,
            "version": self.version,
            "records": [record.as_dict() for record in self.records()],
        }
        return DatasetManifest(
            dataset_id=self.dataset_id,
            version=self.version,
            records=self.records(),
            configuration_hash=stable_hash(payload),
        )

    def verify(self) -> dict[str, Any]:
        missing: list[str] = []
        mismatched: list[str] = []
        for record in self.records():
            path = self._resolve(record.path)
            if not path.is_file():
                missing.append(record.record_id)
                continue
            if file_sha256(path) != record.sha256 or path.stat().st_size != record.byte_size:
                mismatched.append(record.record_id)
        duplicate_ids = len(self._records) != len({record.record_id for record in self.records()})
        return {
            "overall_pass": not missing and not mismatched and not duplicate_ids,
            "dataset_id": self.dataset_id,
            "record_count": len(self._records),
            "missing": missing,
            "mismatched": mismatched,
            "duplicate_record_ids": duplicate_ids,
            "scientific_scope": DATASET_SCOPE,
        }

    def split(self, *, fractions: Mapping[str, float], seed: int = 0) -> dict[str, tuple[DatasetRecord, ...]]:
        """Return deterministic record partitions; files are never duplicated."""

        if not fractions or abs(sum(fractions.values()) - 1.0) > 1e-9:
            raise ValueError("partition fractions must sum to 1")
        if any(value < 0 for value in fractions.values()):
            raise ValueError("partition fractions must be non-negative")
        records = list(self.records())
        random.Random(int(seed)).shuffle(records)
        result: dict[str, tuple[DatasetRecord, ...]] = {}
        cursor = 0
        names = tuple(fractions)
        for index, name in enumerate(names):
            if index == len(names) - 1:
                end = len(records)
            else:
                end = cursor + round(len(records) * fractions[name])
            result[name] = tuple(records[cursor:end])
            cursor = end
        return result

    @classmethod
    def load(cls, root: str | Path) -> "DatasetManager":
        source = Path(root)
        payload = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
        manager = cls(source, dataset_id=str(payload["dataset_id"]), version=str(payload["version"]))
        for item in payload.get("records", ()):
            record = DatasetRecord(
                record_id=str(item["record_id"]),
                role=str(item["role"]),
                path=str(item["path"]),
                sha256=str(item["sha256"]),
                byte_size=int(item["byte_size"]),
                metadata=dict(item.get("metadata", {})),
            )
            manager._records[record.record_id] = record
        return manager

    def _write_files(self) -> None:
        manifest = self.manifest()
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(manifest.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
        checksums = {record.record_id: record.sha256 for record in self.records()}
        self.checksum_path.write_text(json.dumps({"checksums": checksums}, indent=2, sort_keys=True), encoding="utf-8")

    def _relative_or_absolute(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return str(path.resolve())

    def _resolve(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else self.root / path


def merge_dataset_managers(
    managers: Sequence[DatasetManager],
    root: str | Path,
    *,
    dataset_id: str = "merged_dataset",
    version: str = "v2.dataset.merged",
) -> DatasetManager:
    """Merge references by copying existing files into a new managed layout."""

    merged = DatasetManager(root, dataset_id=dataset_id, version=version)
    merged.initialize()
    for manager in managers:
        for record in manager.records():
            source = manager._resolve(record.path)
            merged.register_file(source, record.role, record_id=record.record_id, metadata=record.metadata, copy=True)
    return merged


__all__ = ["DATASET_ROLES", "DATASET_SCOPE", "DatasetManager", "DatasetManifest", "DatasetRecord", "merge_dataset_managers"]
