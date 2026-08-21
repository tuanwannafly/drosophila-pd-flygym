"""Dataset-bound experiment orchestration over the existing study pipeline."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable, Mapping

import yaml

from drosophila_pd.dataset_adapter import DatasetDiscoveryReport, discover_datasets
from drosophila_pd.research_campaign import Campaign
from drosophila_pd.research_pipeline import DatasetInput, StudyOrchestrator, StudyRequest

from .experiment_context import ExperimentContext
from .experiment_events import EventLog, ExperimentEventType
from .experiment_outputs import ExperimentOutputs
from .experiment_session import ExperimentSession, SessionState
from .experiment_summary import ExperimentSummary


StudyRunner = Callable[[StudyRequest, Path, Path], Any]


class ExperimentRuntime:
    """Persist session state and delegate ready experiments once to StudyOrchestrator."""

    def __init__(self, context: ExperimentContext, *, study_runner: StudyRunner | None = None) -> None:
        self.context = context
        self.outputs = ExperimentOutputs(context.output_root)
        self.study_runner = study_runner or self._default_study_runner
        self.session = self._load_session()
        self.events = self._load_events()
        self.discovery: DatasetDiscoveryReport | None = None
        self.validation: Mapping[str, Any] = {}
        self.artifacts: list[Mapping[str, Any]] = []
        self.stages: list[Mapping[str, Any]] = []
        self._load_persisted_summary()

    def discover(self) -> DatasetDiscoveryReport:
        self.discovery = discover_datasets(self.context.dataset_roots)
        return self.discovery

    def prepare(self) -> dict[str, Any]:
        self._ensure_session()
        discovery = self.discover()
        self._bind_or_wait(discovery)
        return self._persist()

    def bind(self) -> dict[str, Any]:
        self._ensure_session()
        discovery = self.discover()
        self._bind_or_wait(discovery)
        return self._persist()

    def run(self) -> dict[str, Any]:
        started = time.perf_counter()
        self._ensure_session()
        discovery = self.discover()
        if not self._bind_or_wait(discovery):
            self.session.duration_seconds = time.perf_counter() - started
            return self._persist()
        try:
            self.session.set_state(SessionState.RUNNING)
            self.events.emit(ExperimentEventType.PIPELINE_STARTED, "Starting existing StudyOrchestrator.")
            request = self._study_request(discovery)
            study_result = self.study_runner(request, self.context.repository_root, self.context.output_root / "study_outputs")
            self.events.emit(ExperimentEventType.PIPELINE_COMPLETED, "StudyOrchestrator completed.")
            self.validation = dict(getattr(study_result, "validation", {}) or {})
            self.events.emit(ExperimentEventType.VALIDATION_COMPLETED, "Study validation output recorded.", validation=self.validation)
            self.artifacts = self.outputs.register_study(study_result)
            self.events.emit(ExperimentEventType.PACKAGE_CREATED, "Research package artifact registered.", artifact_count=len(self.artifacts))
            self.stages = _completed_stages()
            self.session.set_state(SessionState.COMPLETED)
        except Exception as error:  # pragma: no cover - external pipeline controls this path
            self.session.errors.append(f"{type(error).__name__}: {error}")
            self.session.set_state(SessionState.FAILED)
            self.events.emit(ExperimentEventType.FAILED, str(error))
        self.session.duration_seconds = time.perf_counter() - started
        return self._persist()

    def status(self) -> dict[str, Any]:
        if self.session is None:
            return self.prepare()
        return self._persist()

    def summary(self) -> dict[str, Any]:
        self._ensure_session()
        return self._persist()

    def archive(self) -> dict[str, Any]:
        self._ensure_session()
        if self.session.state == SessionState.WAITING_DATASET:
            return self._persist()
        path = self.outputs.archive()
        self.artifacts = [*self.artifacts, {"category": "bundle", "path": path.as_posix(), "byte_size": path.stat().st_size}]
        return self._persist()

    def _default_study_runner(self, request: StudyRequest, repository_root: Path, output_root: Path) -> Any:
        return StudyOrchestrator(repository_root, output_root).run(request)

    def _ensure_session(self) -> None:
        if self.session is None:
            self.session = ExperimentSession(experiment_id=self.context.experiment_id)
            self.events.emit(ExperimentEventType.SESSION_CREATED, "Experiment session created.", session_id=self.session.session_id)

    def _bind_or_wait(self, discovery: DatasetDiscoveryReport) -> bool:
        if discovery.state != "READY":
            self.session.set_state(SessionState.WAITING_DATASET)
            self.session.warnings = list(dict.fromkeys([*self.session.warnings, *discovery.warnings, "No ready dataset is available."]))
            self.events.emit(ExperimentEventType.WAITING_DATASET, "Dataset adapter returned WAITING_DATASET.", missing_types=discovery.missing_types)
            self.stages = [{"stage": name, "status": SessionState.WAITING_DATASET} for name in _stage_names()]
            return False
        self.session.dataset_ids = [dataset.dataset_id for dataset in discovery.datasets]
        self.session.set_state(SessionState.READY)
        self.events.emit(ExperimentEventType.DATASET_READY, "Dataset adapter returned READY.", dataset_ids=self.session.dataset_ids)
        return True

    def _study_request(self, discovery: DatasetDiscoveryReport) -> StudyRequest:
        datasets = tuple(
            DatasetInput(source=dataset.root, dataset_id=dataset.dataset_id, metadata=dict(dataset.manifest))
            for dataset in discovery.datasets
        )
        campaign_payload = _read_campaign(self.context.campaign_config_path)
        campaign_name = str(campaign_payload.get("name", self.context.experiment_id))
        campaign = Campaign(name=campaign_name, metadata=campaign_payload)
        self.session.campaign = campaign.as_dict()
        return StudyRequest(
            study_id=self.context.experiment_id,
            name=campaign_name,
            datasets=datasets,
            campaign=campaign,
            metadata={"experiment_context": self.context.as_dict()},
        )

    def _persist(self) -> dict[str, Any]:
        discovery = self.discovery or self.discover()
        self.outputs.write_json(self.outputs.paths.session, self.session.as_dict())
        self.events.save(self.outputs.paths.execution)
        self.outputs.write_json(self.outputs.paths.runtime_state, {"state": self.session.state, "experiment_id": self.context.experiment_id, "session_id": self.session.session_id})
        if not self.outputs.paths.artifacts.is_file():
            self.outputs.write_empty_artifacts()
        self.outputs.write_json(self.outputs.paths.manifest, {"manifest_version": 1, "context": self.context.as_dict(), "dataset": discovery.as_dict(), "session_id": self.session.session_id})
        summary = ExperimentSummary(
            experiment_id=self.context.experiment_id,
            state=self.session.state,
            dataset=discovery.as_dict(),
            campaign=self.session.campaign,
            duration_seconds=self.session.duration_seconds,
            stages=self.stages,
            validation=self.validation,
            artifacts=self.artifacts,
            warnings=self.session.warnings,
        )
        summary.write(self.outputs.paths.summary_json, self.outputs.paths.summary_markdown)
        return summary.as_dict()

    def _load_session(self) -> ExperimentSession | None:
        return ExperimentSession.load(self.outputs.paths.session) if self.outputs.paths.session.is_file() else None

    def _load_events(self) -> EventLog:
        return EventLog.load(self.outputs.paths.execution) if self.outputs.paths.execution.is_file() else EventLog()

    def _load_persisted_summary(self) -> None:
        if not self.outputs.paths.summary_json.is_file():
            return
        try:
            payload = json.loads(self.outputs.paths.summary_json.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self.validation = dict(payload.get("validation", {}))
        self.artifacts = list(payload.get("artifacts", ()))
        self.stages = list(payload.get("stages", ()))


def _stage_names() -> tuple[str, ...]:
    return ("dataset", "session", "campaign", "study", "research_package")


def _completed_stages() -> list[dict[str, str]]:
    return [{"stage": name, "status": "COMPLETED"} for name in _stage_names()]


def _read_campaign(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["ExperimentRuntime", "StudyRunner"]
