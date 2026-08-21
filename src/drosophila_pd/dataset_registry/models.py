"""Data contracts for the real-dataset intake layer."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


DATASET_CATEGORIES = ("healthy", "pd", "candidate", "control", "validation", "benchmark")
DATASET_BUCKETS = DATASET_CATEGORIES + ("archive", "incoming", "processed", "failed")
MANIFEST_NAMES = ("manifest.json", "dataset_manifest.json")
ROLLOUT_SUFFIXES = {".csv", ".json", ".npz", ".npy"}
DATASET_SCOPE = "Real computational dataset intake and integrity metadata only; not biological validation."


@dataclass(frozen=True, order=True)
class DatasetVersion:
    """Semantic dataset version."""

    value: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"\d+\.\d+\.\d+", self.value):
            raise ValueError(f"dataset version must be semantic versioning: {self.value!r}")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DatasetChecksum:
    """SHA-256 and byte-size record for one dataset file."""

    relative_path: str
    sha256: str
    byte_size: int

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{64}", self.sha256):
            raise ValueError(f"invalid SHA-256 for {self.relative_path!r}")
        if self.byte_size < 0:
            raise ValueError("byte_size must be non-negative")

    def as_dict(self) -> dict[str, Any]:
        return {"relative_path": self.relative_path, "sha256": self.sha256, "byte_size": self.byte_size}


@dataclass(frozen=True)
class DatasetMetadata:
    """Publication and provenance metadata supplied by a dataset owner."""

    dataset_id: str
    dataset_type: str
    version: DatasetVersion
    source: str = ""
    authors: tuple[str, ...] = ()
    license: str = ""
    citation: str = ""
    doi: str = "DOI_PENDING"
    tags: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    version_history: tuple[Mapping[str, Any], ...] = ()
    extras: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls,
        value: Mapping[str, Any] | None,
        *,
        dataset_id: str,
        dataset_type: str,
        version: DatasetVersion,
    ) -> "DatasetMetadata":
        value = value or {}
        authors = value.get("authors", ())
        tags = value.get("tags", ())
        history = value.get("version_history", ())
        return cls(
            dataset_id=str(value.get("dataset_id", dataset_id)),
            dataset_type=str(value.get("dataset_type", dataset_type)),
            version=DatasetVersion(str(value.get("version", version.value))),
            source=str(value.get("source", "")),
            authors=tuple(str(item) for item in authors) if isinstance(authors, (list, tuple)) else (str(authors),),
            license=str(value.get("license", "")),
            citation=str(value.get("citation", "")),
            doi=str(value.get("doi", "DOI_PENDING")),
            tags=tuple(str(item) for item in tags) if isinstance(tags, (list, tuple)) else (str(tags),),
            provenance=dict(value.get("provenance", {})) if isinstance(value.get("provenance", {}), Mapping) else {},
            version_history=tuple(item for item in history if isinstance(item, Mapping)) if isinstance(history, (list, tuple)) else (),
            extras={str(key): item for key, item in value.items() if key not in {
                "dataset_id", "dataset_type", "version", "source", "authors", "license", "citation", "doi", "tags", "provenance", "version_history"
            }},
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "dataset_type": self.dataset_type,
            "version": self.version.value,
            "source": self.source,
            "authors": list(self.authors),
            "license": self.license,
            "citation": self.citation,
            "doi": self.doi,
            "tags": list(self.tags),
            "provenance": dict(self.provenance),
            "version_history": [dict(item) for item in self.version_history],
            **dict(self.extras),
        }


@dataclass(frozen=True)
class DatasetEntry:
    """One file observed in an imported dataset."""

    relative_path: str
    kind: str
    sha256: str | None = None
    byte_size: int | None = None
    experiment_id: str | None = None
    exists: bool = True
    frame_count: int | None = None
    errors: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "relative_path": self.relative_path,
            "kind": self.kind,
            "exists": self.exists,
        }
        for key, value in (("sha256", self.sha256), ("byte_size", self.byte_size), ("experiment_id", self.experiment_id), ("frame_count", self.frame_count)):
            if value is not None:
                result[key] = value
        if self.errors:
            result["errors"] = list(self.errors)
        return result


@dataclass(frozen=True)
class DatasetManifest:
    """Versioned manifest for a registered dataset package."""

    dataset_id: str
    dataset_type: str
    version: DatasetVersion
    status: str
    entries: tuple[DatasetEntry, ...] = ()
    metadata: DatasetMetadata | None = None
    root: Path | None = None
    source: str = ""
    created_at: str = ""
    scientific_scope: str = DATASET_SCOPE
    limitations: tuple[str, ...] = ()
    parse_errors: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any], *, root: str | Path | None = None) -> "DatasetManifest":
        dataset_id = str(value.get("dataset_id", ""))
        dataset_type = str(value.get("dataset_type", ""))
        version = DatasetVersion(str(value.get("dataset_version", value.get("version", "0.0.0"))))
        raw_entries = value.get("entries", value.get("files", ()))
        entries: list[DatasetEntry] = []
        if isinstance(raw_entries, (list, tuple)):
            for item in raw_entries:
                if not isinstance(item, Mapping):
                    continue
                relative = str(item.get("relative_path", item.get("path", "")))
                if not relative:
                    continue
                entries.append(DatasetEntry(
                    relative_path=relative,
                    kind=str(item.get("kind", _kind_for(relative))),
                    sha256=str(item["sha256"]) if item.get("sha256") is not None else None,
                    byte_size=int(item["byte_size"]) if item.get("byte_size") is not None else None,
                    experiment_id=str(item["experiment_id"]) if item.get("experiment_id") is not None else None,
                    exists=bool(item.get("exists", True)),
                    frame_count=int(item["frame_count"]) if item.get("frame_count") is not None else None,
                ))
        metadata_value = value.get("metadata")
        metadata = DatasetMetadata.from_mapping(metadata_value, dataset_id=dataset_id, dataset_type=dataset_type, version=version) if isinstance(metadata_value, Mapping) else None
        return cls(
            dataset_id=dataset_id,
            dataset_type=dataset_type,
            version=version,
            status=str(value.get("status", "WAITING")),
            entries=tuple(entries),
            metadata=metadata,
            root=Path(root).resolve() if root is not None else None,
            source=str(value.get("source", "")),
            created_at=str(value.get("created_at", "")),
            scientific_scope=str(value.get("scientific_scope", DATASET_SCOPE)),
            limitations=tuple(str(item) for item in value.get("limitations", ()) if item is not None),
            parse_errors=tuple(str(item) for item in value.get("parse_errors", ()) if item is not None),
        )

    @property
    def checksums(self) -> tuple[DatasetChecksum, ...]:
        return tuple(
            DatasetChecksum(item.relative_path, item.sha256, item.byte_size)
            for item in self.entries
            if item.sha256 is not None and item.byte_size is not None
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": "1.0",
            "dataset_id": self.dataset_id,
            "dataset_type": self.dataset_type,
            "dataset_version": self.version.value,
            "status": self.status,
            "source": self.source,
            "created_at": self.created_at,
            "entries": [item.as_dict() for item in self.entries],
            "checksums": {item.relative_path: item.sha256 for item in self.entries if item.sha256 is not None},
            "metadata": self.metadata.as_dict() if self.metadata else None,
            "scientific_scope": self.scientific_scope,
            "limitations": list(self.limitations),
            "parse_errors": list(self.parse_errors),
        }


def _kind_for(relative_path: str) -> str:
    lower = relative_path.casefold()
    if "metadata" in lower:
        return "metadata"
    if any(term in lower for term in ("trajectory", "thorax", "rollout", "frame")) and Path(relative_path).suffix.casefold() in ROLLOUT_SUFFIXES:
        return "trajectory"
    if "manifest" in lower or "checksum" in lower:
        return "metadata"
    return "artifact"


__all__ = [
    "DATASET_BUCKETS",
    "DATASET_CATEGORIES",
    "DATASET_SCOPE",
    "DatasetChecksum",
    "DatasetEntry",
    "DatasetManifest",
    "DatasetMetadata",
    "DatasetVersion",
    "MANIFEST_NAMES",
    "ROLLOUT_SUFFIXES",
]
