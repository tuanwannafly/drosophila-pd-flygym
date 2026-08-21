"""Opt-in research automation over existing computational artifacts.

This module is deliberately an orchestration layer.  It composes the existing
experiment, campaign, benchmark, artifact, provenance, and health APIs.  It
does not import FlyGym, run a simulation, create a rollout, or interpret a
biological phenotype.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from drosophila_pd.benchmarking import BENCHMARK_STAGES, BenchmarkSuite
from drosophila_pd.behavior_platform.campaign_artifacts import CampaignArtifactManager, file_sha256
from drosophila_pd.behavior_platform.campaign_provenance import directory_manifest, stable_hash
from drosophila_pd.developer_tooling import ArchitectureSnapshot, DependencyGraphGenerator, ModuleIndex
from drosophila_pd.project_health import ProjectHealth
from drosophila_pd.experiment import (
    ExperimentJob,
    ExperimentQueue,
    ExperimentRunner,
    ExperimentScheduler,
    ExperimentStatus,
)


AUTOMATION_SCOPE = (
    "Research administration and reproducibility metadata only; no simulation, "
    "fabricated rollout, biological validation, or Parkinson's disease claim."
)
DATASET_CATALOG_VERSION = 1
PUBLICATION_SECTIONS = (
    "figures",
    "tables",
    "methods",
    "results",
    "supplementary",
    "references",
    "metadata",
)
AUTOMATION_BENCHMARK_STAGES = BENCHMARK_STAGES + ("Bundle creation",)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _source_hash(path: Path) -> str:
    if path.is_file():
        return file_sha256(path)
    if path.is_dir():
        return stable_hash(directory_manifest(path))
    raise FileNotFoundError(path)


@dataclass(frozen=True)
class DatasetCatalogEntry:
    """Metadata for one caller-provided dataset source."""

    dataset_id: str
    name: str
    version: str
    source: str
    description: str = ""
    sha256: str = ""
    import_date: str = field(default_factory=_timestamp)
    tags: tuple[str, ...] = ()
    species: str = ""
    experiment_type: str = ""
    notes: str = ""
    license: str = ""
    citation: str = ""
    manifest: Mapping[str, Any] = field(default_factory=dict)

    @property
    def imported_at(self) -> str:
        """Compatibility alias for consumers that use timestamp terminology."""

        return self.import_date

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "name": self.name,
            "version": self.version,
            "source": self.source,
            "description": self.description,
            "sha256": self.sha256,
            "import_date": self.import_date,
            "tags": list(self.tags),
            "species": self.species,
            "experiment_type": self.experiment_type,
            "notes": self.notes,
            "license": self.license,
            "citation": self.citation,
            "manifest": _jsonable(self.manifest),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DatasetCatalogEntry":
        return cls(
            dataset_id=str(data["dataset_id"]),
            name=str(data.get("name", data["dataset_id"])),
            version=str(data.get("version", "unknown")),
            source=str(data["source"]),
            description=str(data.get("description", "")),
            sha256=str(data.get("sha256", "")),
            import_date=str(data.get("import_date", data.get("imported_at", _timestamp()))),
            tags=tuple(str(tag) for tag in data.get("tags", ())),
            species=str(data.get("species", "")),
            experiment_type=str(data.get("experiment_type", "")),
            notes=str(data.get("notes", "")),
            license=str(data.get("license", "")),
            citation=str(data.get("citation", "")),
            manifest=dict(data.get("manifest", {})),
        )


class DatasetCatalog:
    """Searchable, version-aware catalog of existing dataset files."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.path = self.root if self.root.suffix.lower() == ".json" else self.root / "dataset_catalog.json"
        self.entries: dict[str, DatasetCatalogEntry] = {}

    def add(
        self,
        source: str | Path,
        *,
        dataset_id: str | None = None,
        name: str | None = None,
        version_name: str = "1",
        version: str | None = None,
        manifest: Mapping[str, Any] | None = None,
        **metadata: Any,
    ) -> DatasetCatalogEntry:
        source_path = Path(source).resolve()
        digest = _source_hash(source_path)
        resolved_name = name or Path(source).stem
        resolved_version = str(version if version is not None else version_name)
        resolved_id = dataset_id or str(uuid.uuid5(uuid.NAMESPACE_URL, f"{source_path}:{resolved_name}:{resolved_version}"))
        if resolved_id in self.entries:
            raise ValueError(f"duplicate dataset_id: {resolved_id}")
        entry = DatasetCatalogEntry(
            dataset_id=resolved_id,
            name=resolved_name,
            version=resolved_version,
            source=source_path.as_posix(),
            description=str(metadata.get("description", "")),
            sha256=digest,
            tags=tuple(str(tag) for tag in metadata.get("tags", ())),
            species=str(metadata.get("species", "")),
            experiment_type=str(metadata.get("experiment_type", "")),
            notes=str(metadata.get("notes", "")),
            license=str(metadata.get("license", "")),
            citation=str(metadata.get("citation", "")),
            manifest=dict(manifest or {}),
        )
        self.entries[dataset_id] = entry
        self.save()
        return entry

    def add_entry(self, entry: DatasetCatalogEntry) -> DatasetCatalogEntry:
        if entry.dataset_id in self.entries:
            raise ValueError(f"duplicate dataset_id: {entry.dataset_id}")
        self.entries[entry.dataset_id] = entry
        self.save()
        return entry

    def list(self) -> tuple[DatasetCatalogEntry, ...]:
        return tuple(self.entries[key] for key in sorted(self.entries))

    def get(self, dataset_id: str) -> DatasetCatalogEntry:
        try:
            return self.entries[dataset_id]
        except KeyError as error:
            raise KeyError(f"unknown dataset_id: {dataset_id}") from error

    def search(self, query: str) -> tuple[DatasetCatalogEntry, ...]:
        needle = str(query).casefold()
        return tuple(
            entry
            for entry in self.list()
            if needle in json.dumps(entry.as_dict(), sort_keys=True).casefold()
        )

    def filter(self, **criteria: Any) -> tuple[DatasetCatalogEntry, ...]:
        return tuple(
            entry
            for entry in self.list()
            if all(getattr(entry, key, None) == value for key, value in criteria.items())
        )

    def group_by(self, field_name: str) -> dict[str, tuple[DatasetCatalogEntry, ...]]:
        groups: dict[str, list[DatasetCatalogEntry]] = {}
        for entry in self.list():
            value = str(getattr(entry, field_name, ""))
            groups.setdefault(value, []).append(entry)
        return {key: tuple(value) for key, value in sorted(groups.items())}

    def versions(self, name: str) -> tuple[DatasetCatalogEntry, ...]:
        return tuple(entry for entry in self.list() if entry.name == name)

    def verify(self, dataset_id: str | None = None) -> dict[str, Any]:
        selected = (self.get(dataset_id),) if dataset_id else self.list()
        rows = []
        for entry in selected:
            source = Path(entry.source)
            exists = source.exists()
            observed = _source_hash(source) if exists else None
            rows.append({
                "dataset_id": entry.dataset_id,
                "exists": exists,
                "expected_sha256": entry.sha256,
                "observed_sha256": observed,
                "pass": exists and observed == entry.sha256,
            })
        return {"overall_pass": all(row["pass"] for row in rows), "datasets": rows, "scope": AUTOMATION_SCOPE}

    def save(self) -> Path:
        return _write_json(self.path, {
            "catalog_version": DATASET_CATALOG_VERSION,
            "entries": [entry.as_dict() for entry in self.list()],
            "scientific_scope": AUTOMATION_SCOPE,
        })

    @classmethod
    def load(cls, path: str | Path) -> "DatasetCatalog":
        catalog = cls(path)
        payload = json.loads(catalog.path.read_text(encoding="utf-8"))
        catalog.entries = {
            entry.dataset_id: entry
            for entry in (DatasetCatalogEntry.from_dict(item) for item in payload.get("entries", ()))
        }
        return catalog


class ExperimentQueueManager:
    """Persistent queue facade over the existing explicit-handler scheduler."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.state_path = self.root / "experiment_queue.json"
        self.jobs: dict[str, ExperimentJob] = {}
        self.events: list[dict[str, Any]] = []

    def enqueue(self, job: ExperimentJob) -> ExperimentJob:
        if job.job_id in self.jobs:
            raise ValueError(f"duplicate job_id: {job.job_id}")
        self.jobs[job.job_id] = job
        self.save()
        return job

    def list(self, status: ExperimentStatus | str | None = None) -> tuple[ExperimentJob, ...]:
        selected = tuple(self.jobs[key] for key in sorted(self.jobs))
        if status is None:
            return selected
        value = ExperimentStatus(status)
        return tuple(job for job in selected if job.status is value)

    def cancel(self, job_id: str) -> ExperimentJob:
        job = self.jobs[job_id]
        if job.status in {ExperimentStatus.PENDING, ExperimentStatus.RETRYING}:
            job.status = ExperimentStatus.CANCELLED
            self.events.append({"event": "cancelled", "job_id": job_id, "timestamp": _timestamp()})
            self.save()
        return job

    def status(self) -> dict[str, Any]:
        counts = {state.value: 0 for state in ExperimentStatus}
        for job in self.jobs.values():
            counts[job.status.value] += 1
        return {"counts": counts, "total": len(self.jobs), "events": len(self.events), "scope": AUTOMATION_SCOPE}

    def checkpoint(self) -> dict[str, Any]:
        payload = {
            "jobs": [job.as_dict() for job in self.list()],
            "events": list(self.events),
        }
        return {**payload, "checkpoint_hash": stable_hash(payload)}

    def run(
        self,
        *,
        stage_handlers: Mapping[str, Callable[[dict[str, Any]], Any]] | None = None,
        runner: ExperimentRunner | None = None,
        retry_failed: bool = True,
        progress_callback: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> tuple[Any, ...]:
        active_runner = runner or ExperimentRunner(stage_handlers)
        jobs = [job for job in self.list() if job.status not in {ExperimentStatus.COMPLETED, ExperimentStatus.CANCELLED}]
        started = time.perf_counter()
        progress: list[dict[str, Any]] = []

        def on_progress(item: Mapping[str, Any]) -> None:
            record = dict(item)
            record["elapsed_seconds"] = time.perf_counter() - started
            completed = int(record.get("completed", 0))
            record["eta_seconds"] = (record["elapsed_seconds"] / completed * (int(record.get("total", 0)) - completed)) if completed else None
            progress.append(record)
            if progress_callback is not None:
                progress_callback(record)

        results = ExperimentScheduler(active_runner).run(
            ExperimentQueue(jobs),
            retry_failed=retry_failed,
            progress_callback=on_progress,
        )
        self.events.extend({"event": "progress", **item} for item in progress)
        self.events.append({"event": "queue_run_completed", "timestamp": _timestamp(), "result_count": len(results)})
        self.save()
        return results

    def save(self) -> Path:
        return _write_json(self.state_path, self.checkpoint())

    @classmethod
    def load(cls, path: str | Path) -> "ExperimentQueueManager":
        manager = cls(path.parent if Path(path).suffix else path)
        source = Path(path) if Path(path).suffix else manager.state_path
        payload = json.loads(source.read_text(encoding="utf-8"))
        manager.jobs = {
            job.job_id: job
            for job in (ExperimentJob.from_dict(item) for item in payload.get("jobs", ()))
        }
        manager.events = list(payload.get("events", ()))
        return manager


class ReproducibilityCenter:
    """Collect environment and hash metadata without importing simulation code."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def collect(
        self,
        *,
        campaign_id: str,
        configuration: Mapping[str, Any],
        dataset_paths: Sequence[str | Path] = (),
        output_paths: Sequence[str | Path] = (),
        seeds: Sequence[int] = (),
        package_names: Sequence[str] = ("drosophila-pd-flygym",),
        environment: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        return {
            "manifest_version": 1,
            "campaign_id": campaign_id,
            "git_commit": self._git("rev-parse", "HEAD"),
            "branch": self._git("rev-parse", "--abbrev-ref", "HEAD"),
            "tag": self._git("describe", "--tags", "--exact-match") or None,
            "python_version": platform.python_version(),
            "package_versions": {name: _package_version(name) for name in package_names},
            "os": platform.platform(),
            "hardware": {
                "processor": platform.processor(),
                "cpu_count": os.cpu_count(),
            },
            "configuration": _jsonable(configuration),
            "configuration_hash": stable_hash(configuration),
            "dataset_checksums": self._hash_paths(dataset_paths),
            "output_hashes": self._hash_paths(output_paths),
            "random_seeds": [int(seed) for seed in seeds],
            "environment": dict(environment or {}),
            "created_at": _timestamp(),
            "scientific_scope": AUTOMATION_SCOPE,
        }

    def write(self, manifest: Mapping[str, Any], path: str | Path) -> Path:
        return _write_json(Path(path), manifest)

    def verify(self, manifest: Mapping[str, Any]) -> dict[str, Any]:
        checks = []
        for key in ("dataset_checksums", "output_hashes"):
            for path_text, expected in manifest.get(key, {}).items():
                path = Path(path_text)
                exists = path.exists()
                observed = _source_hash(path) if exists else None
                checks.append({"category": key, "path": path_text, "pass": exists and observed == expected})
        return {"overall_pass": all(item["pass"] for item in checks), "checks": checks, "scope": AUTOMATION_SCOPE}

    def _hash_paths(self, paths: Sequence[str | Path]) -> dict[str, str]:
        return {Path(path).resolve().as_posix(): _source_hash(Path(path).resolve()) for path in paths}

    def _git(self, *args: str) -> str:
        try:
            result = subprocess.run(["git", *args], cwd=self.root, check=False, capture_output=True, text=True)
        except OSError:
            return ""
        return result.stdout.strip() if result.returncode == 0 else ""


class BenchmarkCenter:
    """Benchmark registered software operations; never invents a workload."""

    def __init__(self) -> None:
        self.suite = BenchmarkSuite()
        self.extra_operations: dict[str, Callable[[], Any]] = {}

    def register(self, name: str, operation: Callable[[], Any]) -> None:
        if name in BENCHMARK_STAGES:
            self.suite.register(name, operation)
        elif name == "Bundle creation":
            if not callable(operation):
                raise TypeError("benchmark operation must be callable")
            self.extra_operations[name] = operation
        else:
            raise ValueError(f"Unknown automation benchmark stage: {name}")

    def run(self, *, iterations: int = 1) -> dict[str, Any]:
        report = self.suite.run(iterations=iterations)
        for name, operation in self.extra_operations.items():
            samples: list[float] = []
            errors: list[str] = []
            for _ in range(max(1, int(iterations))):
                started = time.perf_counter()
                try:
                    operation()
                    samples.append(time.perf_counter() - started)
                except Exception as error:  # pragma: no cover - caller operation controls this path
                    errors.append(f"{type(error).__name__}: {error}")
            report["stages"].append({"name": name, "iterations": max(1, int(iterations)), "samples_seconds": samples, "mean_seconds": sum(samples) / len(samples) if samples else None, "errors": errors})
        report["stage_count"] = len(report["stages"])
        report["complete"] = all(not stage["errors"] for stage in report["stages"])
        report["scope"] = AUTOMATION_SCOPE
        return report

    def not_run_report(self, reason: str = "No caller-supplied operation was registered.") -> dict[str, Any]:
        return {"status": "not_run", "reason": reason, "stages": list(AUTOMATION_BENCHMARK_STAGES), "scope": AUTOMATION_SCOPE}


class ArtifactManager:
    """Stable artifact directory and checksum facade."""

    def __init__(self, root: str | Path) -> None:
        self.manager = CampaignArtifactManager(root)

    @property
    def root(self) -> Path:
        return self.manager.root

    def prepare(self) -> dict[str, Path]:
        return self.manager.prepare()

    def register_file(self, source: str | Path, category: str, *, name: str | None = None) -> Any:
        return self.manager.register_file(source, category, name=name)

    def inventory(self) -> tuple[Any, ...]:
        return self.manager.inventory()

    def write_manifest(self, output_path: str | Path | None = None) -> Path:
        return self.manager.write_manifest(output_path)

    def verify(self) -> dict[str, Any]:
        manifest_path = self.root / "artifact_manifest.json"
        if not manifest_path.is_file():
            return {"overall_pass": False, "reason": "artifact manifest is missing", "scope": AUTOMATION_SCOPE}
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        checks = []
        for item in payload.get("artifacts", []):
            path = Path(item["path"])
            exists = path.is_file()
            observed = file_sha256(path) if exists else None
            checks.append({"path": item["path"], "pass": exists and observed == item["sha256"]})
        return {"overall_pass": all(item["pass"] for item in checks), "checks": checks, "scope": AUTOMATION_SCOPE}


class PublicationBuilder:
    """Package existing publication assets without generating scientific content."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.assets: list[dict[str, Any]] = []

    def prepare(self) -> dict[str, Path]:
        paths = {section: self.root / section for section in PUBLICATION_SECTIONS}
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        return paths

    def register(self, source: str | Path, section: str, *, name: str | None = None, identifier: str | None = None) -> Path:
        if section not in PUBLICATION_SECTIONS:
            raise ValueError(f"unsupported publication section: {section}")
        source_path = Path(source)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        target = self.prepare()[section] / (name or source_path.name)
        if source_path.resolve() != target.resolve():
            target.write_bytes(source_path.read_bytes())
        self.assets.append({"identifier": identifier or target.stem, "section": section, "path": target.relative_to(self.root).as_posix(), "sha256": file_sha256(target), "byte_size": target.stat().st_size})
        return target

    def build(self, *, metadata: Mapping[str, Any] | None = None) -> Path:
        self.prepare()
        payload = {
            "publication_manifest_version": 1,
            "sections": list(PUBLICATION_SECTIONS),
            "assets": list(self.assets),
            "metadata": _jsonable(metadata or {}),
            "scientific_scope": "Existing publication assets only; no scientific content generated.",
        }
        return _write_json(self.root / "manifest.json", payload)


class ProjectHealthMonitor:
    """Expose existing static health checks as an automation endpoint."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def run(self) -> dict[str, Any]:
        report = ProjectHealth(self.root).run()
        report["automation"] = {
            "package_present": (self.root / "pyproject.toml").is_file(),
            "ci_present": (self.root / ".github" / "workflows").is_dir(),
            "scientific_scope": AUTOMATION_SCOPE,
        }
        return report


class DeveloperToolkit:
    """Facade over the existing module, API, dependency, and architecture explorers."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.module_index = ModuleIndex(self.root)

    def module_index_report(self) -> list[dict[str, Any]]:
        return self.module_index.build()

    def api_report(self) -> dict[str, Any]:
        return ArchitectureSnapshot(self.root).api.explore()

    def dependency_report(self) -> dict[str, Any]:
        return DependencyGraphGenerator(self.module_index).build()

    def architecture_report(self) -> dict[str, Any]:
        return ArchitectureSnapshot(self.root).build()

    def test_report(self) -> dict[str, Any]:
        tests = sorted(path.relative_to(self.root).as_posix() for path in (self.root / "tests").glob("test_*.py"))
        return {"test_count": len(tests), "tests": tests, "scope": AUTOMATION_SCOPE}

    def performance_report(self) -> dict[str, Any]:
        return {"status": "caller_supplied_operations_required", "scope": AUTOMATION_SCOPE}


class ResearchAutomationPlatform:
    """Coordinate the Milestone 3 management surfaces."""

    def __init__(self, root: str | Path, output_root: str | Path | None = None) -> None:
        self.root = Path(root).resolve()
        self.output_root = Path(output_root or self.root / "automation_outputs")
        self.catalog = DatasetCatalog(self.output_root / "catalog")
        self.queue = ExperimentQueueManager(self.output_root / "queue")
        self.reproducibility = ReproducibilityCenter(self.root)
        self.health = ProjectHealthMonitor(self.root)
        self.toolkit = DeveloperToolkit(self.root)

    def health_check(self) -> dict[str, Any]:
        return self.health.run()

    def generate_manifest(self) -> dict[str, Any]:
        health = self.health_check()
        architecture = self.toolkit.architecture_report()
        return {
            "automation_manifest_version": 1,
            "created_at": _timestamp(),
            "git_commit": self.reproducibility._git("rev-parse", "HEAD"),
            "health": health,
            "architecture": {"module_count": len(architecture["modules"]), "api_module_count": architecture["api"]["module_count"]},
            "scientific_scope": AUTOMATION_SCOPE,
        }

    def write_manifest(self, path: str | Path | None = None) -> Path:
        return _write_json(Path(path or self.output_root / "automation_manifest.json"), self.generate_manifest())


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


__all__ = [
    "AUTOMATION_BENCHMARK_STAGES",
    "AUTOMATION_SCOPE",
    "ArtifactManager",
    "BenchmarkCenter",
    "DatasetCatalog",
    "DatasetCatalogEntry",
    "DeveloperToolkit",
    "ExperimentQueueManager",
    "ProjectHealthMonitor",
    "PublicationBuilder",
    "ReproducibilityCenter",
    "ResearchAutomationPlatform",
]
