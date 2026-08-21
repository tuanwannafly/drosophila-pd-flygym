"""Dataset-gated orchestration for the V6 campaign execution workflow."""

from __future__ import annotations

import json
import csv
import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np

try:
    import yaml
except ImportError:  # pragma: no cover - declared runtime dependency
    yaml = None

from drosophila_pd.research_pipeline import DatasetInput, StudyOrchestrator, StudyRequest
from drosophila_pd.research_campaign import Campaign
from drosophila_pd.behavior_platform.digital_twin import (
    DigitalTwin,
    TwinConfiguration,
    TwinHistory,
    TwinMetadata,
    TwinState,
)
from drosophila_pd.behavior_platform.measurement import measure_rollout_behavior
from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.digital_twin_platform import DigitalTwinPlatform
from drosophila_pd.parkinson import ParkinsonMotorModel

from .artifact_registry import ArtifactRegistry
from .execution_context import ExecutionContext
from .execution_history import ExecutionHistory
from .execution_result import ExecutionResult
from .execution_state import ExecutionState


EXECUTION_STAGES = (
    "dataset",
    "campaign",
    "study_orchestrator",
    "analysis",
    "statistics",
    "computational_pd",
    "scientific_validation",
    "publication",
    "research_package",
)
PLANNING_STATUSES = {"PLANNING_ONLY", "PLANNED", "RESERVED_FOR_EXECUTION"}
MANIFEST_NAMES = {
    "manifest.json",
    "dataset_manifest.json",
    "manifest.yaml",
    "manifest.yml",
    "dataset_manifest.yaml",
    "dataset_manifest.yml",
}


@dataclass
class DatasetRecord:
    """Manifest-level dataset metadata; rollout contents are never parsed."""

    dataset_id: str
    root: Path
    manifest_path: Path
    manifest: Mapping[str, Any]
    metadata_path: Path | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    checksum_path: Path | None = None
    checksums: Mapping[str, Any] = field(default_factory=dict)
    payload_paths: tuple[Path, ...] = ()
    missing_paths: tuple[Path, ...] = ()
    rollout_paths: tuple[Path, ...] = ()
    reference_path: Path | None = None
    validation: Mapping[str, Any] = field(default_factory=dict)
    status: str = "WAITING_DATASET"
    reason: str = ""

    @property
    def ready(self) -> bool:
        return self.status == "READY"

    def as_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "root": self.root.as_posix(),
            "manifest": self.manifest_path.as_posix(),
            "metadata": self.metadata_path.as_posix() if self.metadata_path else None,
            "checksum": self.checksum_path.as_posix() if self.checksum_path else None,
            "payload_paths": [path.as_posix() for path in self.payload_paths],
            "missing_paths": [path.as_posix() for path in self.missing_paths],
            "rollout_paths": [path.as_posix() for path in self.rollout_paths],
            "reference_path": self.reference_path.as_posix() if self.reference_path else None,
            "validation": dict(self.validation),
            "status": self.status,
            "reason": self.reason,
        }


@dataclass
class DiscoveryReport:
    """Result of manifest-only dataset discovery."""

    state: ExecutionState
    datasets: list[DatasetRecord]
    searched_roots: tuple[Path, ...]
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "datasets": [dataset.as_dict() for dataset in self.datasets],
            "searched_roots": [path.as_posix() for path in self.searched_roots],
            "warnings": list(self.warnings),
            "rollout_parsing": "not performed",
        }


DatasetRunner = Callable[[StudyRequest, Path, Path], Any]


class DatasetDiscovery:
    """Discover executable dataset manifests without reading rollout arrays."""

    def discover(
        self,
        roots: Sequence[str | Path],
        *,
        dataset_type: str | None = None,
    ) -> DiscoveryReport:
        resolved_roots = tuple(Path(root).resolve() for root in roots)
        manifests = []
        for root in resolved_roots:
            if not root.exists():
                continue
            candidates = [root] if root.is_file() else sorted(root.rglob("*"))
            for candidate in candidates:
                if candidate.is_file() and candidate.name in MANIFEST_NAMES:
                    manifests.append(candidate)
        datasets: list[DatasetRecord] = []
        warnings: list[str] = []
        for manifest_path in sorted(set(manifests)):
            payload = _read_structured(manifest_path)
            status = str(payload.get("status", "")).upper()
            if status in PLANNING_STATUSES or payload.get("execution_enabled") is False:
                warnings.append(f"ignored non-executable manifest: {manifest_path.as_posix()}")
                continue
            if dataset_type and payload.get("dataset_type") not in (None, dataset_type):
                continue
            datasets.append(_record_from_manifest(manifest_path, payload))
        ready = [dataset for dataset in datasets if dataset.ready]
        invalid = [dataset for dataset in datasets if dataset.status == "INVALID_DATASET"]
        if not ready and invalid:
            state = ExecutionState.INVALID_DATASET
            warnings.append("Dataset manifests were found but at least one is invalid.")
        else:
            state = ExecutionState.READY if ready else ExecutionState.WAITING_DATASET
        if not ready and not invalid:
            warnings.append("No executable dataset manifest with an available payload was found.")
        return DiscoveryReport(
            state=state,
            datasets=datasets,
            searched_roots=resolved_roots,
            warnings=warnings,
        )


class ExecutionRuntime:
    """Run or report a campaign only after real dataset payloads are present."""

    def __init__(
        self,
        context: ExecutionContext,
        *,
        study_runner: DatasetRunner | None = None,
    ) -> None:
        self.context = context
        self._custom_study_runner = study_runner is not None
        self.study_runner = study_runner or self._default_study_runner

    def discover(self) -> DiscoveryReport:
        dataset_type = str(self.context.metadata.get("dataset_type", "healthy"))
        return DatasetDiscovery().discover(self.context.dataset_search_roots, dataset_type=dataset_type)

    def prepare(self) -> ExecutionResult:
        started = time.perf_counter()
        discovery = self.discover()
        history = ExecutionHistory()
        if discovery.state is ExecutionState.READY:
            history.transition(ExecutionState.READY, "Executable dataset manifest discovered.")
            warnings = discovery.warnings
        else:
            warnings = discovery.warnings
        result = self._result(
            history,
            discovery,
            stages=self._stage_rows(discovery.state),
            duration=time.perf_counter() - started,
            warnings=warnings,
        )
        return self._write_report(result)

    def execute(
        self,
        *,
        limit: int | None = None,
        resume: bool = True,
        retry_failed: bool = True,
    ) -> ExecutionResult:
        started = time.perf_counter()
        discovery = self.discover()
        history = ExecutionHistory()
        if discovery.state is ExecutionState.INVALID_DATASET:
            history.transition(ExecutionState.INVALID_DATASET, "Invalid dataset manifest or payload was found.")
            result = self._result(
                history,
                discovery,
                stages=self._stage_rows(ExecutionState.INVALID_DATASET),
                duration=time.perf_counter() - started,
                warnings=discovery.warnings,
            )
            return self._write_report(result)
        if discovery.state is not ExecutionState.READY:
            result = self._result(
                history,
                discovery,
                stages=self._stage_rows(ExecutionState.WAITING_DATASET),
                duration=time.perf_counter() - started,
                warnings=discovery.warnings,
            )
            return self._write_report(result)

        if not self._custom_study_runner:
            return self._execute_batch(
                discovery,
                history,
                started=started,
                limit=limit,
                resume=resume,
                retry_failed=retry_failed,
            )

        try:
            history.transition(ExecutionState.READY, "Executable dataset manifest discovered.")
            history.transition(ExecutionState.RUNNING, "Delegating to the existing StudyOrchestrator.")
            request = self._study_request(discovery)
            study_result = self.study_runner(request, self.context.repository_root, self.context.output_root / "study_outputs")
            history.transition(ExecutionState.VALIDATING, "Study orchestration returned validation output.")
            validation = dict(getattr(study_result, "validation", {}) or {})
            history.transition(ExecutionState.EXPORTING, "Registering existing orchestration artifacts.")
            registry = ArtifactRegistry(self.context.output_root)
            study_root = Path(getattr(study_result, "study_root", self.context.output_root / "study_outputs"))
            registry.register_tree(study_root)
            bundle = getattr(study_result, "package_path", None)
            if bundle and Path(bundle).is_file():
                registry.register(bundle, "bundle")
            history.transition(ExecutionState.COMPLETED, "Execution artifacts registered.")
            result = self._result(
                history,
                discovery,
                stages=self._stage_rows(ExecutionState.COMPLETED),
                artifacts=[record.as_dict() for record in registry.records],
                validation=validation,
                duration=time.perf_counter() - started,
                warnings=discovery.warnings,
            )
            return self._write_report(result, registry=registry)
        except Exception as error:  # pragma: no cover - exercised by caller-provided integrations
            if history.state in {ExecutionState.RUNNING, ExecutionState.VALIDATING, ExecutionState.EXPORTING}:
                history.transition(ExecutionState.FAILED, f"Execution failed: {error}")
            result = self._result(
                history,
                discovery,
                stages=self._stage_rows(ExecutionState.FAILED),
                duration=time.perf_counter() - started,
                errors=[f"{type(error).__name__}: {error}"],
                warnings=discovery.warnings,
            )
            return self._write_report(result)

    def _execute_batch(
        self,
        discovery: DiscoveryReport,
        history: ExecutionHistory,
        *,
        started: float,
        limit: int | None,
        resume: bool,
        retry_failed: bool,
    ) -> ExecutionResult:
        """Execute each declared real rollout through the existing study API."""

        history.transition(ExecutionState.READY, "Healthy dataset manifests discovered.")
        jobs = [
            (dataset, rollout_path)
            for dataset in discovery.datasets
            if dataset.ready
            for rollout_path in dataset.rollout_paths
        ]
        if not jobs:
            history.transition(ExecutionState.RUNNING, "No declared rollout payloads are executable.")
            history.transition(ExecutionState.FAILED, "Ready manifests did not contain executable rollout files.")
            result = self._result(
                history,
                discovery,
                stages=self._stage_rows(ExecutionState.FAILED),
                duration=time.perf_counter() - started,
                errors=["No executable rollout payloads were found."],
                warnings=discovery.warnings,
            )
            return self._write_report(result)

        selected = jobs[: max(0, int(limit))] if limit is not None else jobs
        if limit is not None and int(limit) == 0:
            selected = []
        history.transition(ExecutionState.RUNNING, "Executing declared Healthy rollouts sequentially.")
        rows: list[dict[str, Any]] = []
        errors: list[str] = []
        for dataset, rollout_path in selected:
            row = self._execute_one_rollout(
                dataset,
                rollout_path,
                resume=resume,
                retry_failed=retry_failed,
            )
            rows.append(row)
            if row["status"] == "FAILED":
                errors.append(f"{row['job_id']}: {row.get('error', 'rollout execution failed')}")

        history.transition(ExecutionState.VALIDATING, "Batch rollout results collected.")
        summary_paths = _write_batch_summary(self.context.output_root, rows, total_jobs=len(jobs))
        history.transition(ExecutionState.EXPORTING, "Batch summaries and existing artifacts registered.")
        registry = ArtifactRegistry(self.context.output_root)
        registry.register_tree(self.context.output_root / "rollouts")
        for path in summary_paths.values():
            registry.register(path, "tables" if path.suffix == ".csv" else "reports")
        registry.write()
        state = ExecutionState.FAILED if errors else ExecutionState.COMPLETED
        history.transition(state, "Batch execution finished.")
        scientific_pass = bool(rows) and not errors and all(row.get("validation_status") == "PASS" for row in rows)
        result = self._result(
            history,
            discovery,
            stages=self._stage_rows(state),
            artifacts=[record.as_dict() for record in registry.records],
            validation={
                "overall_pass": scientific_pass,
                "execution_completed": not errors and bool(rows),
                "completed": sum(row["status"] == "COMPLETED" for row in rows),
                "failed": sum(row["status"] == "FAILED" for row in rows),
                "validation_not_available": sum(row.get("validation_status") == "NOT_AVAILABLE" for row in rows),
                "total_discovered": len(jobs),
                "total_selected": len(selected),
                "scientific_scope": "Existing computational pipeline outputs only; no biological validation claim.",
            },
            duration=time.perf_counter() - started,
            errors=errors,
            warnings=discovery.warnings,
        )
        return self._write_report(result, registry=registry)

    def status(self) -> dict[str, Any]:
        report = self.context.output_root / "execution_report.json"
        if report.is_file():
            return json.loads(report.read_text(encoding="utf-8"))
        return self.prepare().as_dict()

    def report(self) -> dict[str, Any]:
        return self.status()

    def bundle(self) -> dict[str, Any]:
        payload = self.status()
        bundles = [item for item in payload.get("artifacts", ()) if item.get("category") == "bundle"]
        payload["bundle"] = bundles[0] if bundles else None
        if not bundles and payload.get("state") == ExecutionState.WAITING_DATASET.value:
            payload.setdefault("warnings", []).append("Bundle not created because dataset discovery is waiting.")
        return payload

    def _default_study_runner(self, request: StudyRequest, repository_root: Path, output_root: Path) -> Any:
        return StudyOrchestrator(repository_root, output_root).run(request)

    def _study_request(self, discovery: DiscoveryReport) -> StudyRequest:
        ready = [dataset for dataset in discovery.datasets if dataset.ready]
        datasets = tuple(
            DatasetInput(source=dataset.root, dataset_id=dataset.dataset_id, metadata=dict(dataset.manifest))
            for dataset in ready
        )
        campaign_payload = _read_campaign(self.context.campaign_config_path)
        name = str(campaign_payload.get("name", self.context.campaign_id))
        campaign = Campaign(name=name, metadata=campaign_payload)
        return StudyRequest(
            study_id=self.context.campaign_id,
            name=name,
            datasets=datasets,
            campaign=campaign,
            metadata={"execution_context": self.context.as_dict(), "campaign": campaign_payload},
        )

    def _execute_one_rollout(
        self,
        dataset: DatasetRecord,
        rollout_path: Path,
        *,
        resume: bool,
        retry_failed: bool,
    ) -> dict[str, Any]:
        job_id = _job_id(dataset.dataset_id, rollout_path)
        output_root = self.context.output_root / "rollouts" / job_id
        status_path = output_root / "rollout_status.json"
        if resume and status_path.is_file():
            persisted = _read_json(status_path)
            if persisted.get("status") == "COMPLETED":
                return {**persisted, "resumed": True}
            if persisted.get("status") == "FAILED" and not retry_failed:
                return {**persisted, "resumed": True, "retry_skipped": True}

        started = time.perf_counter()
        row: dict[str, Any] = {
            "job_id": job_id,
            "dataset_id": dataset.dataset_id,
            "rollout": rollout_path.as_posix(),
            "status": "RUNNING",
            "output_root": output_root.as_posix(),
            "validation_status": "NOT_STARTED",
        }
        try:
            rollout_metadata = {**dict(dataset.manifest), **dict(dataset.metadata)}
            rollout = _load_rollout(rollout_path, dataset_id=dataset.dataset_id, metadata=rollout_metadata)
            measurements = measure_rollout_behavior(rollout)
            reference = (
                    _load_rollout(dataset.reference_path, dataset_id=f"{dataset.dataset_id}_reference", metadata=rollout_metadata)
                if dataset.reference_path is not None
                else None
            )
            request = self._rollout_request(
                dataset,
                rollout,
                measurements,
                reference=reference,
                study_id=job_id,
            )
            study_result = self.study_runner(request, self.context.repository_root, self.context.output_root / "rollouts")
            study_root = Path(getattr(study_result, "study_root", output_root))
            figure_files = _write_rollout_figures(study_root, rollout, measurements)
            publication_files = _register_publication_figures(study_root, figure_files)
            pipeline_validation = dict(getattr(study_result, "validation", {}) or {})
            scientific_validation = _read_json(study_root / "validation" / "validation_summary.json")
            validation_status = (
                "PASS"
                if scientific_validation.get("overall_pass") is True
                and scientific_validation.get("available", True) is not False
                else "NOT_AVAILABLE"
            )
            row.update(
                {
                    "status": "COMPLETED",
                    "validation_status": validation_status,
                    "validation": {
                        "pipeline": pipeline_validation,
                        "scientific": scientific_validation,
                    },
                    "figures": {name: path.as_posix() for name, path in figure_files.items()},
                    "publication": {name: path.as_posix() for name, path in publication_files.items()},
                    "study_root": study_root.as_posix(),
                    "duration_seconds": time.perf_counter() - started,
                }
            )
        except Exception as error:
            row.update(
                {
                    "status": "FAILED",
                    "validation_status": "NOT_AVAILABLE",
                    "error": f"{type(error).__name__}: {error}",
                    "duration_seconds": time.perf_counter() - started,
                }
            )
        _write_json(status_path, row)
        return row

    def _rollout_request(
        self,
        dataset: DatasetRecord,
        rollout: RolloutData,
        measurements: Mapping[str, Any],
        *,
        reference: RolloutData | None,
        study_id: str,
    ) -> StudyRequest:
        campaign_payload = _read_campaign(self.context.campaign_config_path)
        campaign_name = str(campaign_payload.get("name", self.context.campaign_id))
        campaign = Campaign(name=campaign_name, metadata=campaign_payload)
        speed = measurements.get("trajectory", {}).get("instantaneous_speed_mm_s", ())
        twin_platform = _digital_twin_platform(rollout, dataset, campaign_name)
        return StudyRequest(
            study_id=study_id,
            name=f"{campaign_name}: {rollout.condition_id}",
            datasets=(DatasetInput(source=dataset.root, dataset_id=dataset.dataset_id, metadata={"manifest": dict(dataset.manifest)}),),
            campaign=campaign,
            digital_twin_platform=twin_platform,
            rollouts=(rollout,),
            statistical_samples={"instantaneous_speed_mm_s": [float(value) for value in speed]},
            observed_rollout=rollout,
            reference_rollout=reference,
            computational_pd_model=ParkinsonMotorModel(),
            metadata={
                "execution_context": self.context.as_dict(),
                "dataset_id": dataset.dataset_id,
                "rollout_path": rollout.metadata.get("source_path", ""),
                "scientific_scope": "Real imported rollout post-processing only; no biological validation claim.",
            },
        )

    def _result(
        self,
        history: ExecutionHistory,
        discovery: DiscoveryReport,
        *,
        stages: list[Mapping[str, Any]],
        artifacts: list[Mapping[str, Any]] | None = None,
        validation: Mapping[str, Any] | None = None,
        duration: float = 0.0,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
    ) -> ExecutionResult:
        return ExecutionResult(
            execution_id=self.context.campaign_id,
            state=history.state,
            datasets=[dataset.as_dict() for dataset in discovery.datasets],
            stages=stages,
            artifacts=artifacts or [],
            validation=validation or {"overall_pass": False, "status": history.state.value},
            duration_seconds=duration,
            errors=errors or [],
            warnings=warnings or [],
            history=history.as_dict(),
            context=self.context.as_dict(),
        )

    def _write_report(self, result: ExecutionResult, *, registry: ArtifactRegistry | None = None) -> ExecutionResult:
        self.context.output_root.mkdir(parents=True, exist_ok=True)
        json_path = self.context.output_root / "execution_report.json"
        md_path = self.context.output_root / "execution_report.md"
        json_path.write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(_markdown_report(result), encoding="utf-8")
        active_registry = registry or ArtifactRegistry(self.context.output_root)
        active_registry.register(json_path, "reports")
        active_registry.register(md_path, "reports")
        active_registry.write()
        return result

    @staticmethod
    def _stage_rows(state: ExecutionState) -> list[dict[str, str]]:
        return [{"stage": name, "status": state.value} for name in EXECUTION_STAGES]


def _load_rollout(path: Path, *, dataset_id: str, metadata: Mapping[str, Any]) -> RolloutData:
    """Load one canonical JSON, NPZ, or trajectory CSV rollout."""

    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.casefold() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, Mapping) and isinstance(payload.get("rollout"), Mapping):
            payload = payload["rollout"]
        if not isinstance(payload, Mapping):
            raise ValueError("rollout JSON must contain a mapping")
        data = dict(payload)
        data.setdefault("condition_id", dataset_id)
        data.setdefault("timestep_s", metadata.get("timestep_s", metadata.get("timestep", 0.0)))
        data.setdefault("thorax_positions", data.get("thorax_positions_mm"))
        data.setdefault("thorax_quaternions", data.get("thorax_quaternions_xyzw"))
        data["metadata"] = {**dict(metadata), **dict(data.get("metadata", {})), "source_path": path.as_posix()}
        return RolloutData.from_mapping(data)
    if path.suffix.casefold() == ".npz":
        with np.load(path, allow_pickle=False) as archive:
            arrays = {key: archive[key] for key in archive.files}
        positions = _first_array(arrays, ("thorax_positions", "thorax_positions_mm", "positions"))
        quaternions = _first_array(arrays, ("thorax_quaternions", "quaternions"))
        if positions is None or quaternions is None:
            raise ValueError("NPZ rollout requires thorax_positions and thorax_quaternions")
        timestep = _scalar_array(arrays.get("timestep_s"), metadata.get("timestep_s", metadata.get("timestep")))
        if timestep is None:
            timestep = _timestep_from_time(arrays.get("time_s"))
        if timestep is None:
            raise ValueError("NPZ rollout requires timestep_s or time_s")
        joints = {key[6:]: value for key, value in arrays.items() if key.startswith("joint__")}
        adhesion = {key[9:]: value for key, value in arrays.items() if key.startswith("adhesion__")}
        return RolloutData(
            condition_id=dataset_id,
            timestep_s=timestep,
            thorax_positions=positions,
            thorax_quaternions=quaternions,
            com_positions=_first_array(arrays, ("com_positions", "com_positions_mm")),
            joint_positions=joints,
            adhesion_outputs=adhesion,
            metadata={**dict(metadata), "source_path": path.as_posix()},
        )
    if path.suffix.casefold() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise ValueError("trajectory CSV is empty")
        def column(*names: str) -> list[float]:
            name = next((candidate for candidate in names if candidate in rows[0]), None)
            if name is None:
                raise ValueError(f"trajectory CSV is missing one of: {names}")
            return [float(row[name]) for row in rows]
        positions = np.column_stack([column("x_mm", "x"), column("y_mm", "y"), column("z_mm", "z")])
        heading = np.asarray(column("heading_rad", "heading", "yaw_rad"), dtype=float)
        time_values = np.asarray(column("time_s", "time"), dtype=float)
        timestep = _timestep_from_time(time_values)
        if timestep is None:
            timestep = _scalar_array(None, metadata.get("timestep_s", metadata.get("timestep")))
        if timestep is None:
            raise ValueError("trajectory CSV requires a positive time_s spacing or timestep_s metadata")
        quaternions = np.column_stack(
            [np.cos(heading / 2.0), np.zeros_like(heading), np.zeros_like(heading), np.sin(heading / 2.0)]
        )
        return RolloutData(
            condition_id=dataset_id,
            timestep_s=timestep,
            thorax_positions=positions,
            thorax_quaternions=quaternions,
            metadata={**dict(metadata), "source_path": path.as_posix(), "orientation_source": "heading_rad CSV column"},
        )
    raise ValueError(f"unsupported rollout format: {path.suffix}")


def _first_array(values: Mapping[str, Any], names: Sequence[str]) -> Any | None:
    return next((values[name] for name in names if name in values), None)


def _scalar_array(value: Any, fallback: Any = None) -> float | None:
    candidate = fallback if value is None else value
    if candidate is None:
        return None
    array = np.asarray(candidate, dtype=float).ravel()
    if array.size != 1 or not np.isfinite(array[0]) or array[0] <= 0:
        return None
    return float(array[0])


def _timestep_from_time(value: Any) -> float | None:
    if value is None:
        return None
    times = np.asarray(value, dtype=float).ravel()
    if times.size < 2 or not np.isfinite(times).all():
        return None
    deltas = np.diff(times)
    return float(deltas[0]) if np.all(deltas > 0) and np.allclose(deltas, deltas[0]) else None


def _digital_twin_platform(rollout: RolloutData, dataset: DatasetRecord, campaign_name: str) -> DigitalTwinPlatform:
    platform = DigitalTwinPlatform()
    state = TwinState(
        time_s=0.0,
        state_label="imported_rollout",
        metrics={"sample_count": rollout.sample_count(), "timestep_s": rollout.timestep()},
        parameters={"campaign": campaign_name, "dataset_id": dataset.dataset_id},
        metadata={"scientific_scope": "Imported computational rollout state only."},
    )
    twin = DigitalTwin(
        metadata=TwinMetadata(twin_id=rollout.condition_id, source="imported_flygym_rollout"),
        configuration=TwinConfiguration(
            config_id=f"{dataset.dataset_id}:digital_fly",
            version="1",
            parameters={"condition_id": rollout.condition_id},
        ),
        history=TwinHistory(entries=(state,)),
    )
    platform.twins.register(twin, role="Healthy", source_rollout=str(rollout.metadata.get("source_path", "")))
    return platform


def _write_rollout_figures(study_root: Path, rollout: RolloutData, measurements: Mapping[str, Any]) -> dict[str, Path]:
    """Write figures only from measurements of the imported rollout."""

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = study_root / "figures"
    output.mkdir(parents=True, exist_ok=True)
    trajectory = measurements["trajectory"]
    time_s = np.asarray(trajectory["time_s"], dtype=float)
    positions = rollout.positions_array()
    files: dict[str, Path] = {}

    fig, axis = plt.subplots(figsize=(6, 4), constrained_layout=True)
    axis.plot(positions[:, 0], positions[:, 1])
    axis.set(title="Imported rollout trajectory", xlabel="x (mm)", ylabel="y (mm)")
    axis.axis("equal")
    files["trajectory"] = _save_figure(fig, output / "trajectory.png")

    fig, axis = plt.subplots(figsize=(6, 4), constrained_layout=True)
    axis.plot(time_s, trajectory["instantaneous_speed_mm_s"])
    axis.set(title="Imported rollout velocity", xlabel="time (s)", ylabel="speed (mm/s)")
    files["velocity"] = _save_figure(fig, output / "velocity.png")

    com = rollout.com_array()
    if com is not None:
        fig, axis = plt.subplots(figsize=(6, 4), constrained_layout=True)
        axis.plot(com[:, 0], com[:, 1])
        axis.set(title="Imported rollout center of mass", xlabel="x (mm)", ylabel="y (mm)")
        axis.axis("equal")
        files["com"] = _save_figure(fig, output / "com.png")

    fig, axis = plt.subplots(figsize=(6, 4), constrained_layout=True)
    summary = measurements["walking_summary"]
    labels = ("walking bouts", "pause bouts", "turn bouts")
    values = (summary["bout_count"], summary["pause_count"], measurements["turning_summary"]["turn_bout_count"])
    axis.bar(labels, values)
    axis.set(title="Imported rollout behavior counts", ylabel="count")
    files["behavior"] = _save_figure(fig, output / "behavior.png")

    pd_report = ParkinsonMotorModel().evaluate(rollout)
    indices = pd_report.get("motor_impairment_indices", {})
    numeric_indices = {key: float(value) for key, value in indices.items() if isinstance(value, (int, float)) and np.isfinite(value)}
    if numeric_indices:
        fig, axis = plt.subplots(figsize=(7, 4), constrained_layout=True)
        axis.bar(tuple(numeric_indices), tuple(numeric_indices.values()))
        axis.tick_params(axis="x", labelrotation=45)
        axis.set(title="Computational phenotype indices", ylabel="index")
        files["pd_index"] = _save_figure(fig, output / "pd_index.png")

    validation_figures = sorted((study_root / "validation").glob("*.png"))
    if validation_figures:
        import shutil

        target = output / "validation.png"
        shutil.copy2(validation_figures[0], target)
        files["validation"] = target
    return files


def _save_figure(figure: Any, path: Path) -> Path:
    figure.savefig(path, dpi=160)
    import matplotlib.pyplot as plt

    plt.close(figure)
    return path


def _register_publication_figures(study_root: Path, figures: Mapping[str, Path]) -> dict[str, Path]:
    from drosophila_pd.experiment.artifacts import ArtifactLayout, PublicationAssetManager

    manager = PublicationAssetManager(ArtifactLayout(study_root))
    for name, path in figures.items():
        manager.register_figure(path, identifier=name, caption=f"Computational rollout figure: {name}.")
    return manager.write_manifests()


def _write_batch_summary(root: Path, rows: Sequence[Mapping[str, Any]], *, total_jobs: int) -> dict[str, Path]:
    root.mkdir(parents=True, exist_ok=True)
    completed = sum(row.get("status") == "COMPLETED" for row in rows)
    failed = sum(row.get("status") == "FAILED" for row in rows)
    validation_passed = sum(row.get("validation_status") == "PASS" for row in rows)
    summary = {
        "summary_version": 1,
        "total_discovered": total_jobs,
        "total_selected": len(rows),
        "completed": completed,
        "failed": failed,
        "validation_passed": validation_passed,
        "validation_not_available": sum(row.get("validation_status") == "NOT_AVAILABLE" for row in rows),
        "overall_pass": bool(rows) and completed == len(rows) and validation_passed == len(rows),
        "rows": [_jsonable(row) for row in rows],
        "scientific_scope": "Batch orchestration over imported computational rollout outputs only; no biological claim.",
    }
    paths = {"json": root / "summary.json", "csv": root / "summary.csv", "markdown": root / "summary.md"}
    paths["json"].write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    fields = ("job_id", "dataset_id", "rollout", "status", "validation_status", "duration_seconds", "output_root", "error")
    with paths["csv"].open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})
    lines = ["# Healthy Dataset Execution Summary", "", f"- Discovered: `{total_jobs}`", f"- Selected: `{len(rows)}`", f"- Completed: `{completed}`", f"- Failed: `{failed}`", f"- Validation passed: `{validation_passed}`", "", "| Rollout | Status | Validation |", "| --- | --- | --- |"]
    lines.extend(f"| `{row.get('job_id', '')}` | `{row.get('status', '')}` | `{row.get('validation_status', '')}` |" for row in rows)
    lines.extend(["", "Scope: imported computational rollout post-processing only; no biological validation claim.", ""])
    paths["markdown"].write_text("\n".join(lines), encoding="utf-8")
    return paths


def _job_id(dataset_id: str, rollout_path: Path) -> str:
    raw = f"{dataset_id}__{rollout_path.stem}"
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in raw)


def _is_rollout_path(relative: str) -> bool:
    lower = relative.casefold()
    return Path(relative).suffix.casefold() in {".json", ".npz", ".csv"} and any(
        term in lower for term in ("rollout", "trajectory", "thorax", "raw_rollout")
    )


def _looks_like_rollout_path(relative: str) -> bool:
    lower = relative.casefold()
    return any(term in lower for term in ("rollout", "trajectory", "thorax", "raw_rollout"))


def _safe_resolve(root: Path, value: str) -> Path | None:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    return (root / candidate).resolve()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record_from_manifest(manifest_path: Path, payload: Mapping[str, Any]) -> DatasetRecord:
    root = manifest_path.parent.resolve()
    entries = payload.get("entries", payload.get("payloads", payload.get("files", ())))
    if isinstance(entries, Mapping):
        entries = tuple({"relative_path": key, **(value if isinstance(value, Mapping) else {})} for key, value in entries.items())
    payload_paths: list[Path] = []
    missing_paths: list[Path] = []
    rollout_paths: list[Path] = []
    invalid_reasons: list[str] = []
    validation: dict[str, Any] = {"missing": [], "checksum_mismatches": [], "unsupported": []}
    seen_paths: set[str] = set()
    checksums = payload.get("checksums", {})
    for entry in entries if isinstance(entries, (list, tuple)) else ():
        value = (
            entry.get("relative_path", entry.get("path", entry.get("source", entry.get("file"))))
            if isinstance(entry, Mapping)
            else entry
        )
        if not value:
            invalid_reasons.append("manifest entry has no path")
            continue
        candidate = Path(str(value))
        if candidate.is_absolute() or ".." in candidate.parts:
            invalid_reasons.append(f"unsafe payload path: {value}")
            continue
        resolved = candidate if candidate.is_absolute() else root / candidate
        payload_paths.append(resolved.resolve())
        relative = candidate.as_posix()
        if relative in seen_paths:
            invalid_reasons.append(f"duplicate payload path: {relative}")
        seen_paths.add(relative)
        if _looks_like_rollout_path(relative) and Path(relative).suffix.casefold() not in {".json", ".npz", ".csv"}:
            validation["unsupported"].append(relative)
            invalid_reasons.append(f"unsupported rollout format: {relative}")
        if not resolved.exists():
            missing_paths.append(resolved.resolve())
            validation["missing"].append(str(value))
            continue
        if _is_rollout_path(relative):
            rollout_paths.append(resolved.resolve())
        expected = entry.get("sha256") if isinstance(entry, Mapping) else None
        if expected is None and isinstance(checksums, Mapping):
            expected = checksums.get(relative)
        if expected:
            observed = _sha256(resolved)
            if observed != str(expected):
                validation["checksum_mismatches"].append(relative)
                invalid_reasons.append(f"checksum mismatch: {relative}")
    metadata_path = _first_file(root, ("metadata.json", "metadata.yaml", "metadata.yml"))
    checksum_path = _first_file(root, ("checksum.json", "checksums.json", "checksum.yaml", "checksums.yaml"))
    metadata = _read_structured(metadata_path) if metadata_path else {}
    checksum_records = _read_structured(checksum_path) if checksum_path else {}
    if not payload:
        status, reason = "INVALID_DATASET", "Manifest could not be parsed or is empty."
    elif not payload_paths:
        status, reason = "WAITING_DATASET", "Manifest contains no payload entries."
    elif invalid_reasons:
        status, reason = "INVALID_DATASET", "; ".join(invalid_reasons)
    elif missing_paths:
        status, reason = "WAITING_DATASET", "One or more declared payload paths are missing."
    elif not rollout_paths:
        status, reason = "INVALID_DATASET", "Manifest contains no supported rollout file."
    else:
        status, reason = "READY", "Manifest and declared payload paths are available."
    reference_value = payload.get("reference_rollout", payload.get("reference_path"))
    reference_path = None
    if reference_value:
        reference_path = _safe_resolve(root, str(reference_value))
        if reference_path is None or not reference_path.is_file():
            invalid_reasons.append("declared reference rollout is missing or unsafe")
            status, reason = "INVALID_DATASET", "Declared reference rollout is missing or unsafe."
    validation["rollout_count"] = len(rollout_paths)
    validation["invalid_reasons"] = list(invalid_reasons)
    return DatasetRecord(
        dataset_id=str(payload.get("dataset_id", payload.get("id", root.name))),
        root=root,
        manifest_path=manifest_path.resolve(),
        manifest=payload,
        metadata_path=metadata_path,
        metadata=metadata,
        checksum_path=checksum_path,
        checksums=checksum_records,
        payload_paths=tuple(payload_paths),
        missing_paths=tuple(missing_paths),
        rollout_paths=tuple(rollout_paths),
        reference_path=reference_path,
        validation=validation,
        status=status,
        reason=reason,
    )


def _read_campaign(path: Path) -> dict[str, Any]:
    return _read_structured(path) if path.is_file() else {}


def _read_structured(path: Path) -> dict[str, Any]:
    try:
        if path.suffix.lower() == ".json":
            value = json.loads(path.read_text(encoding="utf-8"))
        elif yaml is not None:
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
        else:  # pragma: no cover - PyYAML is a declared dependency
            return {}
    except Exception:  # malformed external metadata must leave the runtime waiting
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return dict(value) if isinstance(value, Mapping) else {}


def _first_file(root: Path, names: Sequence[str]) -> Path | None:
    for name in names:
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


def _markdown_report(result: ExecutionResult) -> str:
    payload = result.as_dict()
    lines = [
        "# Execution Report",
        "",
        f"- Execution: `{payload['execution_id']}`",
        f"- State: `{payload['state']}`",
        f"- Duration (s): `{payload['duration_seconds']:.6f}`",
        "- Scope: execution orchestration over supplied computational datasets only.",
        "",
        "## Datasets",
        "",
        f"- Discovered: `{len(payload['datasets'])}`",
        f"- Rollout parsing: `{payload['context'].get('rollout_parsing', 'not performed')}`",
        "",
        "## Stages",
        "",
        "| Stage | Status |",
        "| --- | --- |",
    ]
    lines.extend(f"| {item['stage']} | {item['status']} |" for item in payload["stages"])
    lines.extend(["", "## Artifacts", ""])
    if payload["artifacts"]:
        lines.extend(f"- `{item['category']}`: `{item['path']}`" for item in payload["artifacts"])
    else:
        lines.append("- None registered.")
    lines.extend(["", "## Validation", "", f"```json\n{json.dumps(payload['validation'], indent=2, sort_keys=True)}\n```", ""])
    if payload["warnings"]:
        lines.extend(["## Warnings", "", *[f"- {item}" for item in payload["warnings"]], ""])
    if payload["errors"]:
        lines.extend(["## Errors", "", *[f"- {item}" for item in payload["errors"]], ""])
    return "\n".join(lines)


__all__ = ["DatasetDiscovery", "DatasetRecord", "DiscoveryReport", "EXECUTION_STAGES", "ExecutionRuntime"]
