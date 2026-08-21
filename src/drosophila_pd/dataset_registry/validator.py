"""Quality-control checks for imported real datasets."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .models import DATASET_CATEGORIES, DatasetEntry, DatasetManifest
from .scanner import DatasetScanner


@dataclass(frozen=True)
class DatasetHealthReport:
    """Machine-readable dataset health result."""

    dataset_id: str
    status: str
    overall_pass: bool
    checks: Mapping[str, Mapping[str, Any]]
    warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "status": self.status,
            "overall_pass": self.overall_pass,
            "checks": {name: dict(value) for name, value in self.checks.items()},
            "warnings": list(self.warnings),
            "scientific_scope": "Dataset health and integrity checks only; not biological validation.",
        }

    def to_markdown(self) -> str:
        lines = [f"# Dataset Health Report: {self.dataset_id}", "", f"- Status: `{self.status}`", f"- Overall pass: `{str(self.overall_pass).lower()}`", "", "| Check | Pass | Details |", "| --- | --- | --- |"]
        for name, value in self.checks.items():
            passed = bool(value.get("pass"))
            details = "; ".join(f"{key}={item}" for key, item in value.items() if key != "pass")
            lines.append(f"| {name} | `{str(passed).lower()}` | {details} |")
        if self.warnings:
            lines.extend(["", "## Warnings", *[f"- {warning}" for warning in self.warnings]])
        lines.extend(["", "Scientific scope: dataset health and integrity only; no biological validation claim.", ""])
        return "\n".join(lines)


class DatasetValidator:
    """Validate manifests, metadata, payload integrity, and trajectory structure."""

    def validate(self, dataset: DatasetManifest | str | Path) -> DatasetHealthReport:
        manifest = DatasetScanner().scan_manifest(dataset) if isinstance(dataset, (str, Path)) else dataset
        root = manifest.root
        checks: dict[str, dict[str, Any]] = {
            "manifest": self._manifest_check(manifest),
            "metadata": self._metadata_check(manifest),
            "file_completeness": self._file_completeness(manifest),
            "checksums": self._checksum_check(manifest),
            "duplicate_rollouts": self._duplicate_check(manifest),
            "schema": self._schema_check(manifest),
            "trajectory": self._trajectory_check(manifest),
            "payload_quality": self._payload_quality(manifest),
        }
        passed = all(bool(value.get("pass")) for value in checks.values())
        return DatasetHealthReport(
            dataset_id=manifest.dataset_id,
            status="READY" if passed else "FAILED",
            overall_pass=passed,
            checks=checks,
            warnings=tuple(manifest.limitations),
        )

    @staticmethod
    def _manifest_check(manifest: DatasetManifest) -> dict[str, Any]:
        required = {
            "dataset_id": bool(manifest.dataset_id),
            "dataset_type": manifest.dataset_type in DATASET_CATEGORIES,
            "dataset_version": bool(manifest.version.value),
            "entries": bool(manifest.entries),
            "parse_errors": not manifest.parse_errors,
        }
        return {"pass": all(required.values()), **required, "errors": list(manifest.parse_errors)}

    @staticmethod
    def _metadata_check(manifest: DatasetManifest) -> dict[str, Any]:
        metadata_entries = [item.relative_path for item in manifest.entries if item.kind == "metadata" or "metadata" in item.relative_path.casefold()]
        available = manifest.metadata is not None or bool(metadata_entries)
        return {"pass": available, "metadata_entries": metadata_entries, "metadata_object": manifest.metadata is not None}

    @staticmethod
    def _file_completeness(manifest: DatasetManifest) -> dict[str, Any]:
        missing = [item.relative_path for item in manifest.entries if not item.exists or _resolve(manifest, item) is None or not _resolve(manifest, item).is_file()]
        return {"pass": not missing and bool(manifest.entries), "missing": missing, "entry_count": len(manifest.entries)}

    @staticmethod
    def _checksum_check(manifest: DatasetManifest) -> dict[str, Any]:
        missing: list[str] = []
        mismatched: list[str] = []
        size_mismatched: list[str] = []
        for item in manifest.entries:
            path = _resolve(manifest, item)
            if not item.sha256:
                missing.append(item.relative_path)
                continue
            if path is None or not path.is_file():
                continue
            observed = _sha256(path)
            if observed != item.sha256:
                mismatched.append(item.relative_path)
            if item.byte_size is not None and path.stat().st_size != item.byte_size:
                size_mismatched.append(item.relative_path)
        return {"pass": not missing and not mismatched and not size_mismatched, "missing": missing, "mismatched": mismatched, "byte_size_mismatches": size_mismatched}

    @staticmethod
    def _duplicate_check(manifest: DatasetManifest) -> dict[str, Any]:
        entries = [item for item in manifest.entries if item.kind == "trajectory"]
        paths = [item.relative_path for item in entries]
        hashes = [item.sha256 for item in entries if item.sha256]
        duplicate_paths = sorted({path for path in paths if paths.count(path) > 1})
        duplicate_hashes = sorted({digest for digest in hashes if hashes.count(digest) > 1})
        return {"pass": not duplicate_paths and not duplicate_hashes, "duplicate_paths": duplicate_paths, "duplicate_sha256": duplicate_hashes}

    @staticmethod
    def _schema_check(manifest: DatasetManifest) -> dict[str, Any]:
        return {"pass": manifest.dataset_type in DATASET_CATEGORIES and bool(manifest.version.value), "dataset_type": manifest.dataset_type, "version": manifest.version.value}

    @staticmethod
    def _trajectory_check(manifest: DatasetManifest) -> dict[str, Any]:
        trajectories = [item for item in manifest.entries if item.kind == "trajectory"]
        missing_frames = [item.relative_path for item in trajectories if item.frame_count == 0]
        return {"pass": bool(trajectories) and not missing_frames, "trajectory_count": len(trajectories), "empty": missing_frames}

    @staticmethod
    def _payload_quality(manifest: DatasetManifest) -> dict[str, Any]:
        corrupted_json: list[str] = []
        invalid_timestamps: list[str] = []
        missing_frames: list[str] = []
        errors: dict[str, str] = {}
        for item in manifest.entries:
            path = _resolve(manifest, item)
            if path is None or not path.is_file():
                continue
            try:
                if path.suffix.casefold() == ".json":
                    value = json.loads(path.read_text(encoding="utf-8"))
                    timestamps = _timestamps_from_json(value)
                    if timestamps is not None and not _timestamps_valid(timestamps):
                        invalid_timestamps.append(item.relative_path)
                elif path.suffix.casefold() == ".csv":
                    rows = list(csv.DictReader(path.open("r", encoding="utf-8", newline="")))
                    frame_values = _numeric_column(rows, ("frame", "frame_index", "step", "index"))
                    if frame_values and frame_values != list(range(len(frame_values))):
                        missing_frames.append(item.relative_path)
                    timestamps = _numeric_column(rows, ("timestamp", "time", "time_s"))
                    if timestamps and not _timestamps_valid(timestamps):
                        invalid_timestamps.append(item.relative_path)
            except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError, csv.Error) as error:
                errors[item.relative_path] = f"{type(error).__name__}: {error}"
                if path.suffix.casefold() == ".json":
                    corrupted_json.append(item.relative_path)
        return {"pass": not corrupted_json and not invalid_timestamps and not missing_frames and not errors, "corrupted_json": corrupted_json, "invalid_timestamps": invalid_timestamps, "missing_frames": missing_frames, "errors": errors}


def _resolve(manifest: DatasetManifest, entry: DatasetEntry) -> Path | None:
    if manifest.root is None:
        return None
    path = Path(entry.relative_path)
    if path.is_absolute() or ".." in path.parts:
        return None
    return manifest.root / path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _numeric_column(rows: list[Mapping[str, str]], names: tuple[str, ...]) -> list[float | int]:
    name = next((candidate for candidate in names if rows and candidate in rows[0]), None)
    if name is None:
        return []
    values: list[float | int] = []
    for row in rows:
        value = row.get(name, "")
        if value == "":
            return []
        number = float(value)
        values.append(int(number) if number.is_integer() else number)
    return values


def _timestamps_from_json(value: Any) -> list[float] | None:
    if not isinstance(value, Mapping):
        return None
    for name in ("timestamps", "timestamp", "time", "time_s"):
        values = value.get(name)
        if isinstance(values, list):
            return [float(item) for item in values]
    return None


def _timestamps_valid(values: list[float | int]) -> bool:
    return all(math.isfinite(float(item)) for item in values) and all(values[index] >= values[index - 1] for index in range(1, len(values)))


__all__ = ["DatasetHealthReport", "DatasetValidator"]
