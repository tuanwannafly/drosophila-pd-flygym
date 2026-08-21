"""Locate declared rollout artifacts without changing them."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np


ROLLOUT_SUFFIXES = {".csv", ".json", ".npz", ".npy"}
TRAJECTORY_TERMS = ("trajectory", "thorax", "raw_rollout", "rollout_arrays")


@dataclass(frozen=True)
class RolloutFile:
    """A declared or discovered file and its read-only inspection metadata."""

    path: Path
    relative_path: str
    kind: str
    experiment_id: str | None = None
    expected_sha256: str | None = None
    expected_byte_size: int | None = None
    exists: bool = False
    observed_sha256: str | None = None
    observed_byte_size: int | None = None
    frame_count: int | None = None
    frame_count_error: str | None = None
    declared: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path.as_posix(),
            "relative_path": self.relative_path,
            "kind": self.kind,
            "experiment_id": self.experiment_id,
            "expected_sha256": self.expected_sha256,
            "expected_byte_size": self.expected_byte_size,
            "exists": self.exists,
            "observed_sha256": self.observed_sha256,
            "observed_byte_size": self.observed_byte_size,
            "frame_count": self.frame_count,
            "frame_count_error": self.frame_count_error,
            "declared": self.declared,
        }


class RolloutLocator:
    """Resolve manifest entries and inspect only declared trajectory files."""

    def locate(self, root: str | Path, manifest: Mapping[str, Any]) -> tuple[RolloutFile, ...]:
        dataset_root = Path(root).resolve()
        records: list[RolloutFile] = []
        entries = manifest.get("entries", ())
        if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
            entries = ()
        for entry in entries:
            if not isinstance(entry, Mapping):
                continue
            relative = _entry_path(entry)
            if not relative:
                continue
            safe = _safe_relative_path(relative)
            if safe is None:
                records.append(
                    RolloutFile(
                        path=dataset_root / relative,
                        relative_path=relative,
                        kind="invalid",
                        experiment_id=_entry_experiment(entry),
                        expected_sha256=_entry_sha(entry, manifest),
                        expected_byte_size=_entry_size(entry),
                        frame_count_error="entry path must be relative and stay inside dataset root",
                    )
                )
                continue
            path = dataset_root / safe
            records.append(self._inspect(path, safe.as_posix(), entry, manifest, declared=True))

        declared = {record.relative_path for record in records}
        rollout_root = dataset_root / "rollouts"
        if rollout_root.is_dir():
            for path in sorted(rollout_root.rglob("*")):
                if path.is_file() and path.suffix.lower() in ROLLOUT_SUFFIXES:
                    relative = path.relative_to(dataset_root).as_posix()
                    if relative not in declared:
                        records.append(
                            self._inspect(path, relative, {}, manifest, declared=False)
                        )
        return tuple(sorted(records, key=lambda item: item.relative_path))

    def _inspect(
        self,
        path: Path,
        relative: str,
        entry: Mapping[str, Any],
        manifest: Mapping[str, Any],
        *,
        declared: bool,
    ) -> RolloutFile:
        exists = path.is_file()
        observed_size = path.stat().st_size if exists else None
        observed_hash = _sha256(path) if exists else None
        kind = _file_kind(relative)
        frame_count = None
        frame_error = None
        if exists and kind == "trajectory":
            try:
                frame_count = _frame_count(path)
            except (OSError, ValueError, TypeError, KeyError) as error:
                frame_error = f"{type(error).__name__}: {error}"
        return RolloutFile(
            path=path,
            relative_path=relative,
            kind=kind,
            experiment_id=_entry_experiment(entry),
            expected_sha256=_entry_sha(entry, manifest),
            expected_byte_size=_entry_size(entry),
            exists=exists,
            observed_sha256=observed_hash,
            observed_byte_size=observed_size,
            frame_count=frame_count,
            frame_count_error=frame_error,
            declared=declared,
        )


def _entry_path(entry: Mapping[str, Any]) -> str:
    return str(entry.get("relative_path", entry.get("path", entry.get("source", entry.get("file", "")))))


def _entry_experiment(entry: Mapping[str, Any]) -> str | None:
    value = entry.get("experiment_id", entry.get("trial_id"))
    return str(value) if value is not None else None


def _entry_sha(entry: Mapping[str, Any], manifest: Mapping[str, Any]) -> str | None:
    value = entry.get("sha256")
    if value is not None:
        return str(value)
    checksums = manifest.get("checksums", {})
    if isinstance(checksums, Mapping):
        path = _entry_path(entry)
        value = checksums.get(path)
        if value is not None:
            return str(value)
    return None


def _entry_size(entry: Mapping[str, Any]) -> int | None:
    value = entry.get("byte_size", entry.get("size"))
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _safe_relative_path(value: str) -> Path | None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path


def _file_kind(relative: str) -> str:
    lower = relative.casefold()
    if any(term in lower for term in TRAJECTORY_TERMS):
        return "trajectory"
    if "/rollouts/" in f"/{lower}/" and Path(relative).suffix.casefold() in ROLLOUT_SUFFIXES:
        return "trajectory"
    if "metadata" in lower:
        return "metadata"
    if "report" in lower or "validation" in lower:
        return "report"
    return "artifact"


def _frame_count(path: Path) -> int:
    suffix = path.suffix.casefold()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            return sum(1 for _ in csv.DictReader(handle))
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, Mapping):
            for key in ("thorax_positions", "positions", "frames", "trajectory"):
                value = payload.get(key)
                if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                    return len(value)
        raise ValueError("JSON trajectory does not contain a frame sequence")
    if suffix == ".npz":
        with np.load(path, allow_pickle=False) as archive:
            for key in ("thorax_positions", "positions", "frames", "trajectory"):
                if key in archive:
                    return int(len(archive[key]))
            if archive.files:
                return int(len(archive[archive.files[0]]))
        raise ValueError("NPZ trajectory contains no arrays")
    if suffix == ".npy":
        return int(len(np.load(path, allow_pickle=False, mmap_mode="r")))
    raise ValueError(f"unsupported trajectory format: {suffix}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["ROLLOUT_SUFFIXES", "RolloutFile", "RolloutLocator"]
