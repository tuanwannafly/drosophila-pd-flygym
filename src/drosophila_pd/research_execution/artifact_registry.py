"""Filesystem-backed registry for execution artifacts."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


ARTIFACT_CATEGORIES = (
    "reports",
    "figures",
    "tables",
    "validation",
    "publication",
    "bundle",
    "checksums",
)


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class ArtifactRecord:
    """An existing file registered without changing its contents."""

    category: str
    path: str
    byte_size: int
    sha256: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "path": self.path,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "metadata": dict(self.metadata),
        }


class ArtifactRegistry:
    """Register and verify files produced by an execution or its delegate."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.records: list[ArtifactRecord] = []

    def register(
        self,
        path: str | Path,
        category: str,
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> ArtifactRecord:
        if category not in ARTIFACT_CATEGORIES:
            raise ValueError(f"unsupported artifact category: {category}")
        source = Path(path).resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        try:
            relative = source.relative_to(self.root).as_posix()
        except ValueError:
            relative = source.as_posix()
        record = ArtifactRecord(
            category=category,
            path=relative,
            byte_size=source.stat().st_size,
            sha256=_sha256(source),
            metadata=dict(metadata or {}),
        )
        self.records = [item for item in self.records if item.path != record.path]
        self.records.append(record)
        self.records.sort(key=lambda item: (item.category, item.path))
        return record

    def register_tree(self, root: str | Path) -> tuple[ArtifactRecord, ...]:
        """Register existing files beneath *root* using stable category names."""

        base = Path(root).resolve()
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.name == "artifact_registry.json":
                continue
            category = _category_for(path, base)
            self.register(path, category)
        return tuple(self.records)

    def verify(self) -> dict[str, Any]:
        checks = []
        for record in self.records:
            path = Path(record.path)
            if not path.is_absolute():
                path = self.root / path
            exists = path.is_file()
            observed = _sha256(path) if exists else None
            checks.append({"path": record.path, "exists": exists, "pass": exists and observed == record.sha256})
        return {"overall_pass": all(item["pass"] for item in checks), "checks": checks}

    def as_dict(self) -> dict[str, Any]:
        return {
            "artifact_registry_version": 1,
            "created_at": utc_timestamp(),
            "root": self.root.as_posix(),
            "artifacts": [record.as_dict() for record in self.records],
            "verification": self.verify(),
        }

    def write(self, path: str | Path | None = None) -> Path:
        target = Path(path or self.root / "artifact_registry.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target


def _category_for(path: Path, root: Path) -> str:
    parts = path.relative_to(root).parts
    first = parts[0] if parts else "reports"
    if first in ARTIFACT_CATEGORIES:
        return first
    if path.suffix.lower() in {".zip", ".tar", ".gz"}:
        return "bundle"
    if path.suffix.lower() in {".png", ".svg", ".pdf"}:
        return "figures"
    if path.suffix.lower() in {".csv"}:
        return "tables"
    if "checksums" in parts:
        return "checksums"
    if "validation" in parts:
        return "validation"
    return "reports"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["ARTIFACT_CATEGORIES", "ArtifactRecord", "ArtifactRegistry"]
