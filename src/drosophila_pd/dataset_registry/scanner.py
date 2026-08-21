"""Read-only source scanning for dataset intake."""

from __future__ import annotations

import csv
import hashlib
import json
import zipfile
from datetime import UTC, datetime
from dataclasses import replace
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

import yaml

from .models import DATASET_BUCKETS, DATASET_CATEGORIES, MANIFEST_NAMES, ROLLOUT_SUFFIXES, DatasetEntry, DatasetManifest, DatasetMetadata, DatasetVersion, _kind_for


class DatasetScanner:
    """Discover manifests and inspect import sources without writing files."""

    def __init__(self, *, categories: Sequence[str] = DATASET_CATEGORIES) -> None:
        self.categories = tuple(categories)

    def scan(self, root: str | Path) -> tuple[DatasetManifest, ...]:
        """Find manifest-backed datasets below the configured registry root."""

        base = Path(root).resolve()
        manifests: list[DatasetManifest] = []
        search_buckets = tuple(dict.fromkeys((*self.categories, "incoming", "processed", "failed", "archive")))
        for bucket in search_buckets:
            directory = base / bucket
            if not directory.is_dir():
                continue
            for path in sorted(directory.rglob("*")):
                if path.is_file() and path.name in MANIFEST_NAMES:
                    manifests.append(self.scan_manifest(path))
        return tuple({(item.dataset_id, item.root): item for item in manifests}.values())

    def scan_manifest(self, path: str | Path) -> DatasetManifest:
        """Read one manifest and attach its package root."""

        manifest_path = Path(path).resolve()
        parse_errors: tuple[str, ...] = ()
        try:
            value = _read_structured(manifest_path)
        except (OSError, ValueError, yaml.YAMLError) as error:
            value = {}
            parse_errors = (f"{manifest_path.name}: {type(error).__name__}: {error}",)
        manifest = DatasetManifest.from_mapping(value, root=manifest_path.parent)
        if not manifest.entries:
            manifest = self._derive_directory(manifest_path.parent, manifest)
        return replace(manifest, parse_errors=parse_errors or manifest.parse_errors)

    def scan_source(
        self,
        source: str | Path | Sequence[str | Path],
        *,
        dataset_type: str = "incoming",
        dataset_id: str | None = None,
        version: str = "0.1.0",
    ) -> DatasetManifest:
        """Inspect a directory, ZIP, single rollout, or multiple rollouts."""

        if isinstance(source, (list, tuple)):
            paths = tuple(Path(item).resolve() for item in source)
            return self._manifest_for_files(paths, dataset_type=dataset_type, dataset_id=dataset_id, version=version)
        path = Path(source).resolve()
        if path.is_dir():
            manifests = [candidate for candidate in path.rglob("*") if candidate.is_file() and candidate.name in MANIFEST_NAMES]
            if manifests:
                return self.scan_manifest(sorted(manifests)[0])
            return self._derive_directory(path, self._empty_manifest(path, dataset_type, dataset_id, version))
        if path.suffix.casefold() == ".zip":
            return self._scan_zip(path, dataset_type=dataset_type, dataset_id=dataset_id, version=version)
        if path.is_file():
            return self._manifest_for_files((path,), dataset_type=dataset_type, dataset_id=dataset_id, version=version)
        raise FileNotFoundError(path)

    def _scan_zip(self, path: Path, *, dataset_type: str, dataset_id: str | None, version: str) -> DatasetManifest:
        with zipfile.ZipFile(path) as archive:
            names = tuple(item for item in archive.namelist() if not item.endswith("/"))
            _ensure_safe_archive_names(names)
            manifest_name = next((name for name in names if PurePosixPath(name).name in MANIFEST_NAMES), None)
            if manifest_name:
                value = _read_json_bytes(archive.read(manifest_name), manifest_name)
                manifest = DatasetManifest.from_mapping(value, root=None)
                if manifest.entries:
                    return manifest
            entries = tuple(self._entry_from_bytes(name, archive.read(name)) for name in names if PurePosixPath(name).name not in MANIFEST_NAMES)
        return DatasetManifest(
            dataset_id=dataset_id or path.stem,
            dataset_type=dataset_type,
            version=DatasetVersion(version),
            status="WAITING",
            entries=entries,
            source=path.as_posix(),
            created_at=datetime.now(UTC).isoformat(),
        )

    def _derive_directory(self, root: Path, manifest: DatasetManifest) -> DatasetManifest:
        files = tuple(path for path in sorted(root.rglob("*")) if path.is_file() and path.name not in MANIFEST_NAMES and path.name not in {"checksum.json", "checksums.sha256"})
        entries = tuple(self._entry_from_path(root, path) for path in files)
        metadata = manifest.metadata or self._metadata_from_directory(root, manifest)
        return DatasetManifest(
            dataset_id=manifest.dataset_id or root.name,
            dataset_type=manifest.dataset_type or "incoming",
            version=manifest.version,
            status=manifest.status,
            entries=entries,
            metadata=metadata,
            root=root.resolve(),
            source=manifest.source or root.as_posix(),
            created_at=manifest.created_at or datetime.now(UTC).isoformat(),
            scientific_scope=manifest.scientific_scope,
            limitations=manifest.limitations,
            parse_errors=manifest.parse_errors,
        )

    def _manifest_for_files(self, paths: Sequence[Path], *, dataset_type: str, dataset_id: str | None, version: str) -> DatasetManifest:
        entries = tuple(self._entry_from_path(path.parent, path) for path in paths)
        return DatasetManifest(
            dataset_id=dataset_id or (paths[0].stem if paths else "dataset"),
            dataset_type=dataset_type,
            version=DatasetVersion(version),
            status="WAITING",
            entries=entries,
            source=paths[0].as_posix() if paths else "",
            created_at=datetime.now(UTC).isoformat(),
        )

    @staticmethod
    def _empty_manifest(root: Path, dataset_type: str, dataset_id: str | None, version: str) -> DatasetManifest:
        return DatasetManifest(dataset_id=dataset_id or root.name, dataset_type=dataset_type, version=DatasetVersion(version), status="WAITING", root=root)

    @staticmethod
    def _entry_from_path(root: Path, path: Path) -> DatasetEntry:
        relative = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
        payload = path.read_bytes()
        return DatasetEntry(
            relative_path=relative,
            kind=_kind_for(relative),
            sha256=hashlib.sha256(payload).hexdigest(),
            byte_size=len(payload),
            frame_count=_frame_count(path),
        )

    @staticmethod
    def _entry_from_bytes(name: str, payload: bytes) -> DatasetEntry:
        return DatasetEntry(relative_path=name, kind=_kind_for(name), sha256=hashlib.sha256(payload).hexdigest(), byte_size=len(payload))

    @staticmethod
    def _metadata_from_directory(root: Path, manifest: DatasetManifest) -> DatasetMetadata | None:
        for name in ("metadata.json", "metadata.yaml", "metadata.yml"):
            path = root / name
            if path.is_file():
                try:
                    value = _read_structured(path)
                except (OSError, ValueError, yaml.YAMLError):
                    return None
                return DatasetMetadata.from_mapping(value, dataset_id=manifest.dataset_id, dataset_type=manifest.dataset_type, version=manifest.version)
        return None


def _read_structured(path: Path) -> dict[str, Any]:
    if path.suffix.casefold() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
    else:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    return dict(value) if isinstance(value, Mapping) else {}


def _read_json_bytes(payload: bytes, name: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as error:
        raise ValueError(f"invalid JSON manifest {name}: {error}") from error
    return dict(value) if isinstance(value, Mapping) else {}


def _ensure_safe_archive_names(names: Iterable[str]) -> None:
    for name in names:
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"unsafe archive member: {name}")


def _frame_count(path: Path) -> int | None:
    if path.suffix.casefold() not in ROLLOUT_SUFFIXES:
        return None
    try:
        if path.suffix.casefold() == ".csv":
            with path.open("r", encoding="utf-8", newline="") as handle:
                return sum(1 for _ in csv.DictReader(handle))
        if path.suffix.casefold() == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, list):
                return len(value)
            if isinstance(value, Mapping):
                for key in ("frames", "trajectory", "positions", "thorax_positions"):
                    sequence = value.get(key)
                    if isinstance(sequence, Sequence) and not isinstance(sequence, (str, bytes)):
                        return len(sequence)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return None
    return None


__all__ = ["DatasetScanner"]
