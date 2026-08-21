"""Read-only validation for FlyGym dataset manifests and rollout files."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from .flygym_dataset import DATASET_TYPES, FlyGymDataset


@dataclass(frozen=True)
class DatasetValidationReport:
    """Machine-readable validation findings."""

    dataset_id: str
    overall_pass: bool
    checks: Mapping[str, Mapping[str, Any]]
    warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "overall_pass": self.overall_pass,
            "checks": {name: dict(value) for name, value in self.checks.items()},
            "warnings": list(self.warnings),
            "scientific_scope": "Read-only dataset integrity checks; no biological validation claim.",
        }


class DatasetValidator:
    """Validate structure, checksums, metadata, trajectories, and frame counts."""

    def validate(self, dataset: FlyGymDataset) -> DatasetValidationReport:
        manifest = dataset.manifest
        checks: dict[str, dict[str, Any]] = {}
        checks["manifest"] = self._manifest_check(dataset)
        checks["schema_version"] = self._schema_check(manifest)
        checks["metadata"] = {
            "pass": dataset.metadata.available,
            "file_count": len(dataset.metadata.files),
            "errors": list(dataset.metadata.errors),
        }
        checks["missing_files"] = self._missing_check(dataset)
        checks["duplicate_files"] = self._duplicate_check(dataset)
        checks["checksums"] = self._checksum_check(dataset)
        checks["trajectory_files"] = self._trajectory_check(dataset)
        checks["frame_counts"] = self._frame_check(dataset)
        warnings = list(dataset.warnings)
        untracked = [item.relative_path for item in dataset.rollout_files if not item.declared]
        if untracked:
            warnings.append(f"unlisted rollout files found: {len(untracked)}")
        return DatasetValidationReport(
            dataset_id=dataset.dataset_id,
            overall_pass=all(bool(item.get("pass")) for item in checks.values()),
            checks=checks,
            warnings=tuple(warnings),
        )

    @staticmethod
    def _manifest_check(dataset: FlyGymDataset) -> dict[str, Any]:
        required = (
            "dataset_id",
            "dataset_type",
            "dataset_version",
            "source_commit",
            "entries",
            "checksums",
            "citation",
            "scientific_scope",
        )
        missing = [name for name in required if name not in dataset.manifest]
        valid_type = dataset.dataset_type in DATASET_TYPES
        return {"pass": not missing and valid_type, "missing_fields": missing, "dataset_type_valid": valid_type}

    @staticmethod
    def _schema_check(manifest: Mapping[str, Any]) -> dict[str, Any]:
        value = manifest.get("schema_version", manifest.get("manifest_version"))
        valid = bool(value) and bool(re.fullmatch(r"\d+(?:\.\d+)*", str(value)))
        return {"pass": valid, "observed": value, "expected": "numeric schema_version or manifest_version"}

    @staticmethod
    def _missing_check(dataset: FlyGymDataset) -> dict[str, Any]:
        missing = [item.relative_path for item in dataset.rollout_files if not item.exists]
        return {"pass": not missing, "missing": missing}

    @staticmethod
    def _duplicate_check(dataset: FlyGymDataset) -> dict[str, Any]:
        paths = [item.relative_path for item in dataset.rollout_files if item.declared]
        hashes = [item.observed_sha256 for item in dataset.rollout_files if item.declared and item.observed_sha256]
        duplicate_paths = sorted({path for path in paths if paths.count(path) > 1})
        duplicate_hashes = sorted({digest for digest in hashes if hashes.count(digest) > 1})
        return {"pass": not duplicate_paths and not duplicate_hashes, "duplicate_paths": duplicate_paths, "duplicate_sha256": duplicate_hashes}

    @staticmethod
    def _checksum_check(dataset: FlyGymDataset) -> dict[str, Any]:
        mismatches = []
        missing_checksums = []
        size_mismatches = []
        for item in dataset.rollout_files:
            if not item.declared:
                continue
            if not item.expected_sha256:
                missing_checksums.append(item.relative_path)
            elif item.exists and item.observed_sha256 != item.expected_sha256:
                mismatches.append(item.relative_path)
            if item.exists and item.expected_byte_size is not None and item.observed_byte_size != item.expected_byte_size:
                size_mismatches.append(item.relative_path)
        return {"pass": not missing_checksums and not mismatches and not size_mismatches, "missing": missing_checksums, "mismatched": mismatches, "byte_size_mismatches": size_mismatches}

    @staticmethod
    def _trajectory_check(dataset: FlyGymDataset) -> dict[str, Any]:
        files = dataset.trajectory_files
        existing = [item.relative_path for item in files if item.exists]
        return {"pass": bool(files) and len(existing) == len(files), "declared": len(files), "existing": existing}

    @staticmethod
    def _frame_check(dataset: FlyGymDataset) -> dict[str, Any]:
        errors = {item.relative_path: item.frame_count_error for item in dataset.trajectory_files if item.frame_count_error}
        counts = {item.relative_path: item.frame_count for item in dataset.trajectory_files if item.frame_count is not None}
        valid = bool(counts) and not errors and all(int(value) > 0 for value in counts.values())
        return {"pass": valid, "frame_counts": counts, "errors": errors}


__all__ = ["DatasetValidationReport", "DatasetValidator"]
