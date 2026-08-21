"""Registry, import, organization, and artifact generation for real datasets."""

from __future__ import annotations

import csv
import json
import shutil
import zipfile
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from .index import DatasetIndex
from .models import DATASET_BUCKETS, DATASET_CATEGORIES, DatasetEntry, DatasetManifest, DatasetMetadata, DatasetVersion
from .scanner import DatasetScanner, _ensure_safe_archive_names
from .validator import DatasetHealthReport, DatasetValidator


@dataclass(frozen=True)
class DatasetImportResult:
    """Result of an explicit import request."""

    manifest: DatasetManifest
    destination: Path
    health: DatasetHealthReport
    source_kind: str

    @property
    def status(self) -> str:
        return self.health.status

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.manifest.dataset_id,
            "dataset_type": self.manifest.dataset_type,
            "version": self.manifest.version.value,
            "destination": self.destination.as_posix(),
            "source_kind": self.source_kind,
            "status": self.status,
            "health": self.health.as_dict(),
        }


class DatasetRegistry:
    """Manage real dataset intake without simulating or fabricating payloads."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.scanner = DatasetScanner()
        self.validator = DatasetValidator()
        self.index = DatasetIndex()

    def initialize_layout(self) -> Path:
        """Create only the declared storage folders; no data is generated."""

        for bucket in DATASET_BUCKETS:
            (self.root / bucket).mkdir(parents=True, exist_ok=True)
        return self.root

    def scan(self) -> tuple[DatasetManifest, ...]:
        manifests = self.scanner.scan(self.root)
        self.index = DatasetIndex(list(manifests))
        return manifests

    def register(self, manifest: DatasetManifest) -> DatasetManifest:
        return self.index.add(manifest)

    def search(self, query: str = "", **filters: Any) -> tuple[DatasetManifest, ...]:
        return self.index.search(query, **filters)

    def import_directory(
        self,
        source: str | Path,
        *,
        dataset_type: str = "incoming",
        dataset_id: str | None = None,
        version: str = "0.1.0",
    ) -> DatasetImportResult:
        source_path = Path(source).resolve()
        if not source_path.is_dir():
            raise NotADirectoryError(source_path)
        preview = self.scanner.scan_source(source_path, dataset_type=dataset_type, dataset_id=dataset_id, version=version)
        effective_type = preview.dataset_type if preview.dataset_type in DATASET_CATEGORIES else dataset_type
        target = self._new_destination(preview.dataset_id or dataset_id or source_path.name, preview.version.value, effective_type)
        shutil.copytree(source_path, target)
        return self._finalize(target, effective_type, preview.dataset_id or dataset_id or source_path.name, preview.version.value, "directory")

    def import_zip(
        self,
        source: str | Path,
        *,
        dataset_type: str = "incoming",
        dataset_id: str | None = None,
        version: str = "0.1.0",
    ) -> DatasetImportResult:
        source_path = Path(source).resolve()
        if not source_path.is_file() or source_path.suffix.casefold() != ".zip":
            raise ValueError(f"ZIP source required: {source_path}")
        preview = self.scanner.scan_source(source_path, dataset_type=dataset_type, dataset_id=dataset_id, version=version)
        effective_type = preview.dataset_type if preview.dataset_type in DATASET_CATEGORIES else dataset_type
        target = self._new_destination(preview.dataset_id or dataset_id or source_path.stem, preview.version.value, effective_type)
        with zipfile.ZipFile(source_path) as archive:
            names = tuple(item for item in archive.namelist() if not item.endswith("/"))
            _ensure_safe_archive_names(names)
            archive.extractall(target)
        return self._finalize(target, effective_type, preview.dataset_id or dataset_id or source_path.stem, preview.version.value, "zip")

    def import_rollout(
        self,
        source: str | Path,
        *,
        dataset_type: str = "incoming",
        dataset_id: str | None = None,
        version: str = "0.1.0",
        metadata: Mapping[str, Any] | None = None,
    ) -> DatasetImportResult:
        return self.import_rollouts((source,), dataset_type=dataset_type, dataset_id=dataset_id, version=version, metadata=metadata)

    def import_rollouts(
        self,
        sources: Sequence[str | Path],
        *,
        dataset_type: str = "incoming",
        dataset_id: str | None = None,
        version: str = "0.1.0",
        metadata: Mapping[str, Any] | None = None,
    ) -> DatasetImportResult:
        paths = tuple(Path(item).resolve() for item in sources)
        if not paths or any(not path.is_file() for path in paths):
            raise FileNotFoundError("all rollout sources must be existing files")
        target = self._new_destination(dataset_id or paths[0].stem, version, dataset_type)
        rollout_dir = target / "rollouts"
        rollout_dir.mkdir(parents=True, exist_ok=True)
        for path in paths:
            shutil.copy2(path, rollout_dir / path.name)
        if metadata is not None:
            (target / "metadata.json").write_text(json.dumps(dict(metadata), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return self._finalize(target, dataset_type, dataset_id or paths[0].stem, version, "rollout" if len(paths) == 1 else "rollouts")

    def health_report(self, dataset: DatasetManifest | str | Path) -> DatasetHealthReport:
        return self.validator.validate(dataset)

    def write_artifacts(self, dataset: DatasetManifest | str | Path, output: str | Path) -> dict[str, Path]:
        """Write requested registry reports to an explicit output directory."""

        manifest = self.scanner.scan_manifest(dataset) if isinstance(dataset, (str, Path)) else dataset
        report = self.validator.validate(manifest)
        output_path = Path(output).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        paths = {
            "manifest": output_path / "manifest.json",
            "summary": output_path / "dataset_summary.json",
            "inventory": output_path / "dataset_inventory.csv",
            "checksums": output_path / "checksums.sha256",
            "report": output_path / "dataset_report.md",
            "health": output_path / "dataset_health.json",
            "missing": output_path / "missing_data_report.md",
            "duplicates": output_path / "duplicate_report.md",
            "validation": output_path / "validation_report.md",
            "storage": output_path / "storage_report.md",
        }
        paths["manifest"].write_text(json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary = {"dataset": manifest.as_dict(), "health": report.as_dict(), "entry_count": len(manifest.entries), "trajectory_count": sum(item.kind == "trajectory" for item in manifest.entries)}
        paths["summary"].write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with paths["inventory"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("relative_path", "kind", "sha256", "byte_size", "experiment_id", "frame_count", "exists"))
            writer.writeheader()
            for entry in manifest.entries:
                writer.writerow({field: entry.as_dict().get(field, "") for field in writer.fieldnames})
        paths["checksums"].write_text("".join(f"{entry.sha256 or 'MISSING'}  {entry.relative_path}\n" for entry in manifest.entries), encoding="utf-8")
        paths["report"].write_text(report.to_markdown(), encoding="utf-8")
        paths["health"].write_text(json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        missing = report.checks.get("file_completeness", {}).get("missing", [])
        duplicates = report.checks.get("duplicate_rollouts", {})
        paths["missing"].write_text("# Missing Data Report\n\n" + ("\n".join(f"- {item}" for item in missing) if missing else "No missing files reported.") + "\n", encoding="utf-8")
        paths["duplicates"].write_text("# Duplicate Report\n\n" + ("\n".join(f"- {item}" for item in duplicates.get("duplicate_sha256", [])) if duplicates.get("duplicate_sha256") else "No duplicate rollout hashes reported.") + "\n", encoding="utf-8")
        paths["validation"].write_text(report.to_markdown(), encoding="utf-8")
        total_bytes = sum(item.byte_size or 0 for item in manifest.entries)
        paths["storage"].write_text(f"# Storage Report\n\n- Dataset: `{manifest.dataset_id}`\n- Entries: `{len(manifest.entries)}`\n- Declared bytes: `{total_bytes}`\n", encoding="utf-8")
        return paths

    def _new_destination(self, dataset_id: str, version: str, dataset_type: str) -> Path:
        bucket = dataset_type if dataset_type in DATASET_BUCKETS else "incoming"
        target = self.root / bucket / dataset_id / version
        if target.exists():
            raise FileExistsError(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        return target

    def _finalize(self, target: Path, dataset_type: str, dataset_id: str, version: str, source_kind: str) -> DatasetImportResult:
        manifest = self.scanner.scan_source(target, dataset_type=dataset_type, dataset_id=dataset_id, version=version)
        manifest = replace(manifest, dataset_id=dataset_id, dataset_type=dataset_type, version=DatasetVersion(version), root=target, source=source_kind)
        report = self.validator.validate(manifest)
        manifest = replace(manifest, status=report.status)
        (target / "manifest.json").write_text(json.dumps(manifest.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (target / "checksums.sha256").write_text("".join(f"{entry.sha256 or 'MISSING'}  {entry.relative_path}\n" for entry in manifest.entries), encoding="utf-8")
        self.register(manifest)
        return DatasetImportResult(manifest, target, report, source_kind)


__all__ = ["DatasetImportResult", "DatasetRegistry"]
