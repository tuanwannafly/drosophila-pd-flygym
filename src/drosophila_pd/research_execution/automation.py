"""Batch orchestration and progress persistence for prepared campaigns.

This module is intentionally a thin layer over :mod:`execution_runtime`.  It
reads campaign plans and supplied dataset manifests, executes only available
datasets, and records resumable job metadata.  It never creates rollout data
or invokes FlyGym.
"""

from __future__ import annotations

import csv
import json
import re
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from .execution_context import ExecutionContext
from .execution_runtime import DatasetDiscovery, DatasetRecord, ExecutionRuntime


JOB_STATUSES = ("WAITING", "READY", "RUNNING", "COMPLETED", "FAILED")
EXPERIMENT_ID_PATTERN = re.compile(r"^(?P<prefix>[A-Za-z][A-Za-z0-9-]*)_\[(?P<start>\d+)-(?P<end>\d+)\]$")
SCIENTIFIC_SCOPE = (
    "Batch orchestration over supplied computational datasets only; no rollout "
    "generation, simulation execution, or biological claim."
)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    return value


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


@dataclass(frozen=True)
class CampaignPlan:
    """Rows loaded from one existing campaign definition."""

    campaign_id: str
    campaign_path: Path
    metadata: Mapping[str, Any] = field(default_factory=dict)
    rows: tuple[Mapping[str, Any], ...] = ()

    @property
    def experiment_count(self) -> int:
        return len(self.rows)

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "campaign_path": self.campaign_path.as_posix(),
            "experiment_count": self.experiment_count,
            "rows": [_jsonable(row) for row in self.rows],
        }


@dataclass
class ExecutionJob:
    """Persisted unit of campaign work.

    A job represents one campaign matrix row and is deliberately independent
    of simulation state.  The ``dataset`` field is the supplied dataset ID.
    """

    id: str
    dataset: str
    seed: int | None = None
    status: str = "WAITING"
    start_time: str | None = None
    end_time: str | None = None
    duration: float | None = None
    artifacts: Mapping[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    error: str = ""
    quality_gates: Mapping[str, Any] = field(default_factory=dict)
    expected_outputs: tuple[str, ...] = ()
    validation_profile: str = ""

    def __post_init__(self) -> None:
        self.status = str(self.status).upper()
        if self.status not in JOB_STATUSES:
            raise ValueError(f"unsupported execution job status: {self.status}")

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "dataset": self.dataset,
            "seed": self.seed,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "artifacts": _jsonable(self.artifacts),
            "retry_count": self.retry_count,
            "error": self.error,
            "quality_gates": _jsonable(self.quality_gates),
            "expected_outputs": list(self.expected_outputs),
            "validation_profile": self.validation_profile,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "ExecutionJob":
        return cls(
            id=str(payload["id"]),
            dataset=str(payload["dataset"]),
            seed=_optional_int(payload.get("seed")),
            status=str(payload.get("status", "WAITING")),
            start_time=payload.get("start_time"),
            end_time=payload.get("end_time"),
            duration=_optional_float(payload.get("duration")),
            artifacts=dict(payload.get("artifacts", {})),
            retry_count=int(payload.get("retry_count", 0)),
            error=str(payload.get("error", "")),
            quality_gates=dict(payload.get("quality_gates", {})),
            expected_outputs=tuple(str(item) for item in payload.get("expected_outputs", ())),
            validation_profile=str(payload.get("validation_profile", "")),
        )


class ExecutionQueue:
    """Small persistent FIFO queue with sequential execution semantics."""

    def __init__(self, root: str | Path, *, parallel: bool = False) -> None:
        self.root = Path(root)
        self.path = self.root if self.root.suffix.lower() == ".json" else self.root / "jobs.json"
        self.jobs: dict[str, ExecutionJob] = {}
        self.parallel = bool(parallel)

    def enqueue(self, job: ExecutionJob) -> ExecutionJob:
        if job.id in self.jobs:
            raise ValueError(f"duplicate execution job: {job.id}")
        self.jobs[job.id] = job
        return job

    def get(self, job_id: str) -> ExecutionJob:
        return self.jobs[job_id]

    def ordered(self) -> tuple[ExecutionJob, ...]:
        return tuple(self.jobs[key] for key in sorted(self.jobs))

    def pending(self) -> tuple[ExecutionJob, ...]:
        return tuple(job for job in self.ordered() if job.status in {"WAITING", "READY", "FAILED"})

    def counts(self) -> dict[str, int]:
        return {status: sum(job.status == status for job in self.jobs.values()) for status in JOB_STATUSES}

    def save(self) -> Path:
        return _write_json(self.path, {
            "queue_version": 1,
            "jobs": [job.as_dict() for job in self.ordered()],
            "sequential_default": True,
            "parallel_execution": self.parallel,
            "parallel_note": "Reserved for a future scheduler; current execution remains sequential.",
            "scientific_scope": SCIENTIFIC_SCOPE,
        })

    @classmethod
    def load(cls, path: str | Path) -> "ExecutionQueue":
        source = Path(path)
        payload = json.loads(source.read_text(encoding="utf-8"))
        queue = cls(source, parallel=bool(payload.get("parallel_execution", False)))
        queue.jobs = {
            job.id: job
            for job in (ExecutionJob.from_dict(item) for item in payload.get("jobs", ()))
        }
        return queue


def load_campaign_plan(context: ExecutionContext) -> CampaignPlan:
    """Load the configured campaign matrix without inventing experiment IDs."""

    exact_path = context.campaign_root / context.campaign_id / "campaign.yaml"
    if exact_path.is_file():
        config_path = exact_path
    elif context.campaign_id == "experimental_campaign_01_healthy_baseline":
        config_path = context.campaign_config_path
    else:
        return CampaignPlan(context.campaign_id, exact_path.parent, {}, ())
    metadata = _read_structured(config_path)
    campaign_dir = config_path.parent
    matrix_name = metadata.get("experiment_matrix", "experiment_matrix.csv")
    matrix_path = campaign_dir / str(matrix_name)
    rows = _read_matrix(matrix_path) if matrix_path.is_file() else _expand_pattern(metadata)
    normalized = tuple(_normalize_plan_row(row) for row in rows)
    return CampaignPlan(context.campaign_id, campaign_dir, metadata, normalized)


class ResearchAutomation:
    """Extend :class:`ExecutionRuntime` with resumable campaign bookkeeping."""

    def __init__(
        self,
        context: ExecutionContext,
        *,
        progress_root: str | Path | None = None,
        runtime: ExecutionRuntime | None = None,
        parallel: bool = False,
    ) -> None:
        self.context = context
        self.progress_root = Path(progress_root or context.repository_root / "results" / "progress").resolve()
        self.runtime = runtime or ExecutionRuntime(context)
        self.queue = ExecutionQueue(self.progress_root, parallel=parallel)

    @property
    def queue_path(self) -> Path:
        return self.progress_root / "jobs.json"

    def plan(self, *, resume: bool = True) -> CampaignPlan:
        campaign = load_campaign_plan(self.context)
        if resume and self.queue_path.is_file():
            self.queue = ExecutionQueue.load(self.queue_path)
        for row in campaign.rows:
            job_id = str(row["experiment_id"])
            if job_id not in self.queue.jobs:
                self.queue.enqueue(ExecutionJob(
                    id=job_id,
                    dataset=job_id,
                    seed=_optional_int(row.get("seed")),
                    expected_outputs=tuple(_split_list(row.get("expected_outputs", ()))),
                    validation_profile=str(row.get("validation_profile", "")),
                ))
        self.queue.save()
        return campaign

    def execute(
        self,
        *,
        limit: int | None = None,
        resume: bool = True,
        retry_failed: bool = True,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        campaign = self.plan(resume=resume)
        discovery = DatasetDiscovery().discover(self.context.dataset_search_roots)
        records = {record.dataset_id: record for record in discovery.datasets}
        self._refresh_readiness(records, resume=resume, retry_failed=retry_failed)
        attempts = 0
        for job in self.queue.ordered():
            if limit is not None and attempts >= max(0, int(limit)):
                break
            if job.status == "COMPLETED":
                continue
            if job.status == "FAILED" and not retry_failed:
                continue
            record = records.get(job.dataset)
            if record is None or not record.ready:
                job.status = "FAILED" if record and record.status == "INVALID_DATASET" else "WAITING"
                if record and record.status == "INVALID_DATASET":
                    job.error = record.reason
                continue
            if job.status == "FAILED":
                job.retry_count += 1
            attempts += 1
            self._execute_job(job, record, resume=resume, retry_failed=retry_failed)
            self.queue.save()
            self._write_progress(campaign, started=started)
        self.queue.save()
        return self._write_progress(campaign, started=started)

    run = execute

    def progress(self) -> dict[str, Any]:
        campaign = self.plan(resume=True)
        return self._write_progress(campaign, started=time.perf_counter())

    status = progress

    def _refresh_readiness(
        self,
        records: Mapping[str, DatasetRecord],
        *,
        resume: bool,
        retry_failed: bool,
    ) -> None:
        for job in self.queue.ordered():
            if job.status == "COMPLETED" and resume:
                continue
            record = records.get(job.dataset)
            if record is None:
                job.status = "WAITING"
                job.error = "Dataset manifest not discovered."
            elif record.status == "INVALID_DATASET":
                job.status = "FAILED"
                job.error = record.reason
            elif record.ready and (job.status != "FAILED" or retry_failed):
                job.status = "READY"
                job.error = ""
            else:
                job.status = "WAITING"

    def _execute_job(
        self,
        job: ExecutionJob,
        dataset: DatasetRecord,
        *,
        resume: bool,
        retry_failed: bool,
    ) -> None:
        job.status = "RUNNING"
        job.start_time = _timestamp()
        started = time.perf_counter()
        job_root = self.context.output_root / "rollouts" / job.id
        gates: dict[str, Any] = {
            "dataset_valid": dataset.ready,
            "viewer_export": False,
            "analysis": False,
            "validation": False,
            "publish": False,
        }
        artifacts: dict[str, Any] = {}
        try:
            viewer_path = job_root / "viewer_pose.json"
            try:
                from drosophila_pd.viewer_export import export_viewer_pose

                exported = export_viewer_pose(dataset.root, viewer_path)
                gates["viewer_export"] = bool(exported.validation.overall_pass)
                if gates["viewer_export"]:
                    artifacts["viewer_pose.json"] = viewer_path.as_posix()
            except (FileNotFoundError, ValueError, OSError) as error:
                job.error = f"viewer export: {type(error).__name__}: {error}"

            if not gates["viewer_export"]:
                raise RuntimeError("quality gate failed: viewer export is not valid")

            rows = []
            for rollout_path in dataset.rollout_paths:
                rows.append(self.runtime._execute_one_rollout(
                    dataset,
                    rollout_path,
                    resume=resume,
                    retry_failed=retry_failed,
                ))
            if not rows:
                raise RuntimeError("quality gate failed: dataset has no rollout payload")
            roots = [Path(row.get("study_root", row.get("output_root", ""))) for row in rows]
            gates["analysis"] = all(_has_files(root / "analysis") for root in roots)
            validation_payloads = [_read_json(root / "validation" / "validation_summary.json") for root in roots]
            gates["validation"] = all(
                _has_files(root / "validation")
                and payload.get("overall_pass") is True
                and payload.get("available", True) is not False
                for root, payload in zip(roots, validation_payloads)
            )
            gates["publish"] = all(gates[name] for name in ("dataset_valid", "viewer_export", "analysis", "validation"))
            artifacts.update(_artifact_inventory(roots, include_publication=gates["publish"]))
            if not all((row.get("status") == "COMPLETED") for row in rows):
                raise RuntimeError("analysis pipeline returned a failed rollout")
            job.artifacts = artifacts
            job.quality_gates = gates
            job.status = "COMPLETED"
            if not gates["publish"]:
                job.error = "Publication blocked by one or more quality gates."
        except Exception as error:
            job.status = "FAILED"
            job.error = job.error or f"{type(error).__name__}: {error}"
            job.artifacts = artifacts
            job.quality_gates = gates
        finally:
            job.end_time = _timestamp()
            job.duration = time.perf_counter() - started
            _write_json(job_root / "automation_job.json", job.as_dict())

    def _write_progress(self, campaign: CampaignPlan, *, started: float) -> dict[str, Any]:
        counts = self.queue.counts()
        durations = [job.duration for job in self.queue.ordered() if job.status == "COMPLETED" and job.duration]
        remaining = counts["WAITING"] + counts["READY"] + counts["RUNNING"]
        eta = (sum(durations) / len(durations) * remaining) if durations else None
        payload = {
            "progress_version": 1,
            "campaign_id": campaign.campaign_id,
            "campaign_path": campaign.campaign_path.as_posix(),
            "total": len(self.queue.jobs),
            "completed": counts["COMPLETED"],
            "running": counts["RUNNING"],
            "failed": counts["FAILED"],
            "waiting": counts["WAITING"] + counts["READY"],
            "ready": counts["READY"],
            "estimated_remaining_seconds": eta,
            "jobs": [job.as_dict() for job in self.queue.ordered()],
            "scientific_scope": SCIENTIFIC_SCOPE,
        }
        self.progress_root.mkdir(parents=True, exist_ok=True)
        _write_json(self.progress_root / "progress.json", payload)
        fields = ("id", "dataset", "seed", "status", "start_time", "end_time", "duration", "retry_count", "error")
        with (self.progress_root / "progress.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for job in self.queue.ordered():
                writer.writerow({field: job.as_dict().get(field, "") for field in fields})
        self._write_progress_markdown(payload)
        self._write_research_summary(payload)
        return payload

    def _write_progress_markdown(self, payload: Mapping[str, Any]) -> Path:
        lines = [
            "# Research Progress",
            "",
            f"- Campaign: `{payload['campaign_id']}`",
            f"- Total: `{payload['total']}`",
            f"- Completed: `{payload['completed']}`",
            f"- Running: `{payload['running']}`",
            f"- Failed: `{payload['failed']}`",
            f"- Waiting: `{payload['waiting']}`",
            f"- Estimated remaining seconds: `{payload['estimated_remaining_seconds']}`",
            "",
            "| Job | Dataset | Status | Retries |",
            "| --- | --- | --- | ---: |",
        ]
        lines.extend(
            f"| `{job['id']}` | `{job['dataset']}` | `{job['status']}` | {job['retry_count']} |"
            for job in payload["jobs"]
        )
        lines.extend(["", f"Scope: {SCIENTIFIC_SCOPE}", ""])
        path = self.progress_root / "progress.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    def _write_research_summary(self, payload: Mapping[str, Any]) -> Path:
        condition_totals: dict[str, int] = {}
        completed_by_condition: dict[str, int] = {}
        for job in payload["jobs"]:
            match = re.match(r"^(?P<condition>[A-Za-z][A-Za-z0-9-]*)_\d+$", job["dataset"])
            condition = match.group("condition") if match else "unknown"
            condition_totals[condition] = condition_totals.get(condition, 0) + 1
            if job["status"] == "COMPLETED":
                completed_by_condition[condition] = completed_by_condition.get(condition, 0) + 1
        lines = [
            "# Research Summary",
            "",
            f"- Total datasets: `{payload['total']}`",
            *[
                f"- {name} completed: `{completed_by_condition.get(name, 0)}` / `{total}`"
                for name, total in sorted(condition_totals.items())
            ],
            f"- Failed: `{payload['failed']}`",
            f"- Pending: `{payload['waiting'] + payload['running']}`",
            "",
            "## Artifacts",
            "",
            "Artifacts are listed per job in `progress.json` and in each job's `automation_job.json`.",
            "",
            "## Scientific Scope",
            "",
            SCIENTIFIC_SCOPE,
            "",
        ]
        path = self.progress_root / "research_summary.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path


AutomationRunner = ResearchAutomation


def _read_structured(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
    else:
        try:
            import yaml

            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except ImportError:  # pragma: no cover - PyYAML is a runtime dependency
            payload = {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _read_matrix(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _expand_pattern(metadata: Mapping[str, Any]) -> list[dict[str, Any]]:
    match = EXPERIMENT_ID_PATTERN.fullmatch(str(metadata.get("experiment_id_pattern", "")))
    if match is None:
        return []
    start, end = int(match.group("start")), int(match.group("end"))
    width = len(match.group("start"))
    seed_policy = metadata.get("seed_policy", {})
    seed_start = 0
    if isinstance(seed_policy, Mapping):
        values = str(seed_policy.get("values", "0")).split("-", 1)
        seed_start = int(values[0])
    return [
        {"experiment_id": f"{match.group('prefix')}_{index:0{width}d}", "seed": seed_start + offset, "status": "PLANNED"}
        for offset, index in enumerate(range(start, end + 1))
    ]


def _normalize_plan_row(row: Mapping[str, Any]) -> dict[str, Any]:
    identifier = row.get("experiment_id", row.get("id", row.get("dataset")))
    if not identifier:
        raise ValueError("campaign matrix row is missing experiment_id")
    return {
        **dict(row),
        "experiment_id": str(identifier),
        "seed": _optional_int(row.get("seed")),
    }


def _split_list(value: Any) -> list[str]:
    if isinstance(value, (tuple, list, set)):
        return [str(item) for item in value]
    return [item.strip() for item in str(value or "").split(";") if item.strip()]


def _optional_int(value: Any) -> int | None:
    if value in (None, "", "None"):
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value in (None, "", "None"):
        return None
    return float(value)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, Mapping) else {}


def _artifact_inventory(roots: Sequence[Path], *, include_publication: bool) -> dict[str, list[str]]:
    inventory: dict[str, list[str]] = {name: [] for name in ("analysis", "statistics", "validation", "report", "publication")}
    for root in roots:
        for category in inventory:
            directory = root / ("reports" if category == "report" else category)
            if category == "publication" and not include_publication:
                continue
            if directory.is_dir():
                inventory[category].extend(path.as_posix() for path in sorted(directory.rglob("*")) if path.is_file())
    return inventory


def _has_files(path: Path) -> bool:
    return path.is_dir() and any(item.is_file() for item in path.rglob("*"))


__all__ = [
    "AutomationRunner",
    "CampaignPlan",
    "ExecutionJob",
    "ExecutionQueue",
    "JOB_STATUSES",
    "ResearchAutomation",
    "SCIENTIFIC_SCOPE",
    "load_campaign_plan",
]
