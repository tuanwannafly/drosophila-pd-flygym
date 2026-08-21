"""Explicit-handler experiment runner, queue, and resumable scheduler."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any, Mapping

from drosophila_pd.behavior_platform.campaign_provenance import current_git_commit, stable_hash

from .artifacts import ArtifactLayout
from .models import (
    ExperimentJob,
    ExperimentManifest,
    ExperimentResult,
    ExperimentStatus,
    STAGE_NAMES,
    _jsonable,
    utc_timestamp,
)


StageHandler = Callable[[dict[str, Any]], Any]


class ExperimentLogger:
    """Append structured JSON events for one experiment."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, *, job_id: str, level: str = "INFO", **metadata: Any) -> None:
        record = {
            "timestamp": utc_timestamp(),
            "event": event,
            "job_id": job_id,
            "level": level,
            "metadata": _jsonable(metadata),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


class ExperimentQueue:
    """FIFO queue of jobs; it does not execute work itself."""

    def __init__(self, jobs: Iterable[ExperimentJob] = ()) -> None:
        self._jobs: list[ExperimentJob] = []
        for job in jobs:
            self.add(job)

    def add(self, job: ExperimentJob) -> None:
        if any(existing.job_id == job.job_id for existing in self._jobs):
            raise ValueError(f"duplicate job_id: {job.job_id}")
        self._jobs.append(job)

    def next(self) -> ExperimentJob | None:
        return self._jobs.pop(0) if self._jobs else None

    def requeue(self, job: ExperimentJob) -> None:
        self._jobs.append(job)

    def __len__(self) -> int:
        return len(self._jobs)

    def pending(self) -> tuple[ExperimentJob, ...]:
        return tuple(self._jobs)


class ExperimentRunner:
    """Run caller-supplied stages in the canonical experiment order.

    The runner deliberately has no FlyGym import and no default handler. A
    real FlyGym pipeline must be injected as the ``stage_handlers`` mapping.
    Each handler receives a mutable context containing the job, artifact paths,
    and previous stage summaries, and must return JSON-compatible metadata or a
    path to an artifact it created.
    """

    def __init__(self, stage_handlers: Mapping[str, StageHandler] | None = None) -> None:
        self.stage_handlers = dict(stage_handlers or {})
        unknown = sorted(set(self.stage_handlers) - set(STAGE_NAMES))
        if unknown:
            raise ValueError(f"unknown stage handler(s): {unknown}")

    def run(self, job: ExperimentJob) -> ExperimentResult:
        layout = ArtifactLayout(job.job_root)
        paths = layout.prepare()
        logger = ExperimentLogger(paths["logs"] / "experiment.jsonl")
        started_at = utc_timestamp()
        job.status = ExperimentStatus.RUNNING
        job.attempts += 1
        job.updated_at = started_at
        _write_json(job.job_root / "job.json", job.as_dict())
        logger.log("experiment_started", job_id=job.job_id, attempt=job.attempts)
        stage_results: dict[str, Any] = {}
        error: str | None = None
        try:
            missing = [stage for stage in STAGE_NAMES if stage not in self.stage_handlers]
            if missing:
                raise RuntimeError(
                    "No default simulation pipeline is installed; provide explicit handlers for: "
                    + ", ".join(missing)
                )
            context: dict[str, Any] = {
                "job": job,
                "config": dict(job.config),
                "paths": paths,
                "stage_results": stage_results,
            }
            for stage in STAGE_NAMES:
                logger.log("stage_started", job_id=job.job_id, stage=stage)
                output = self.stage_handlers[stage](context)
                serialized = _jsonable(output)
                stage_results[stage] = serialized
                _write_json(paths["reports"] / f"{stage}.json", serialized)
                logger.log("stage_completed", job_id=job.job_id, stage=stage)
            job.status = ExperimentStatus.COMPLETED
            logger.log("experiment_completed", job_id=job.job_id, attempt=job.attempts)
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
            job.status = ExperimentStatus.FAILED
            logger.log("experiment_failed", job_id=job.job_id, level="ERROR", error=error)
            _write_json(paths["reports"] / "error.json", {"error": error})
        finished_at = utc_timestamp()
        job.updated_at = finished_at
        artifact_hashes = layout.inventory()
        manifest = ExperimentManifest(
            job_id=job.job_id,
            status=job.status,
            attempt=job.attempts,
            stages=stage_results,
            artifact_hashes={name: item["sha256"] for name, item in artifact_hashes.items()},
            configuration_hash=stable_hash(job.config),
            git_commit=current_git_commit(),
            started_at=started_at,
            finished_at=finished_at,
            error=error,
            metadata=job.metadata,
        )
        _write_json(layout.manifest_path, manifest.as_dict())
        _write_json(job.job_root / "job.json", job.as_dict())
        return ExperimentResult(
            job_id=job.job_id,
            status=job.status,
            stages=stage_results,
            artifact_paths={name: str(path) for name, path in paths.items()},
            manifest_path=layout.manifest_path,
            error=error,
        )


class ExperimentScheduler:
    """Deterministic sequential scheduler with retry and resume semantics."""

    def __init__(self, runner: ExperimentRunner) -> None:
        self.runner = runner

    def run(
        self,
        queue: ExperimentQueue,
        *,
        skip_finished: bool = True,
        retry_failed: bool = True,
        progress_callback: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> tuple[ExperimentResult, ...]:
        results: list[ExperimentResult] = []
        total = len(queue)
        completed = 0
        while (job := queue.next()) is not None:
            if skip_finished and job.status == ExperimentStatus.COMPLETED:
                completed += 1
                continue
            result = self.runner.run(job)
            results.append(result)
            if result.status == ExperimentStatus.FAILED and retry_failed and job.attempts <= job.max_retries:
                job.status = ExperimentStatus.RETRYING
                queue.requeue(job)
                progress_status = ExperimentStatus.RETRYING.value
            else:
                completed += 1
                progress_status = result.status.value
            if progress_callback is not None:
                progress_callback(
                    {
                        "job_id": job.job_id,
                        "status": progress_status,
                        "completed": completed,
                        "total": total,
                    }
                )
        return tuple(results)

    def resume(self, jobs: Iterable[ExperimentJob], **kwargs: Any) -> tuple[ExperimentResult, ...]:
        """Resume jobs from their in-memory persisted status."""

        return self.run(ExperimentQueue(jobs), **kwargs)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True), encoding="utf-8")


__all__ = [
    "ExperimentLogger",
    "ExperimentQueue",
    "ExperimentRunner",
    "ExperimentScheduler",
    "StageHandler",
]
