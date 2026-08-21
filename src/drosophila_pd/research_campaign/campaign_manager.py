"""Campaign lifecycle, scheduling, validation, and publication packaging."""

from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping

from drosophila_pd.behavior_platform.campaign_provenance import file_sha256

from .campaign import CAMPAIGN_SCOPE, Campaign, ExperimentSpec
from .campaign_events import CampaignEvent
from .campaign_history import CampaignHistory
from .campaign_manifest import CampaignManifest, build_manifest
from .campaign_state import CampaignState

Executor = Callable[[ExperimentSpec], Mapping[str, Any]]


class CampaignManager:
    """Manage campaign plans without executing simulation implicitly.

    A caller may inject an executor for already-approved software stages. When
    no executor is provided, lifecycle methods only update orchestration state.
    """

    def __init__(self, root: str | Path = "campaigns") -> None:
        self.root = Path(root)
        self.campaigns: dict[str, Campaign] = {}
        self.histories: dict[str, CampaignHistory] = {}

    def create(self, campaign: Campaign) -> Campaign:
        if campaign.campaign_id in self.campaigns:
            raise ValueError(f"duplicate campaign_id: {campaign.campaign_id}")
        self.campaigns[campaign.campaign_id] = campaign
        self.histories[campaign.campaign_id] = CampaignHistory(campaign.campaign_id)
        self._emit(campaign, "created", payload={"name": campaign.name})
        return campaign

    def get(self, campaign_id: str) -> Campaign:
        try:
            return self.campaigns[campaign_id]
        except KeyError as error:
            raise KeyError(f"unknown campaign_id: {campaign_id}") from error

    def add_experiment(self, campaign_id: str, experiment: ExperimentSpec) -> ExperimentSpec:
        campaign = self.get(campaign_id)
        for dependency in experiment.dependencies:
            if dependency == experiment.experiment_id:
                raise ValueError("experiment cannot depend on itself")
        campaign.add_experiment(experiment)
        self._emit(campaign, "experiment_added", experiment_id=experiment.experiment_id)
        return experiment

    def queue(self, campaign_id: str) -> dict[str, Any]:
        campaign = self.get(campaign_id)
        self._validate_dependencies(campaign)
        campaign.status = CampaignState.QUEUED
        for experiment in campaign.experiments:
            if experiment.state not in {CampaignState.COMPLETED, CampaignState.CANCELLED}:
                experiment.state = CampaignState.QUEUED
        self._refresh_ready(campaign)
        self._emit(campaign, "queued", state=campaign.status.value)
        return self.dashboard(campaign_id)

    def next_ready(self, campaign_id: str) -> tuple[ExperimentSpec, ...]:
        campaign = self.get(campaign_id)
        self._refresh_ready(campaign)
        return tuple(
            sorted(
                (item for item in campaign.experiments if item.state == CampaignState.READY),
                key=lambda item: (-item.priority, item.batch, item.experiment_id),
            )
        )

    def run(
        self,
        campaign_id: str,
        executor: Executor | None = None,
        *,
        max_experiments: int | None = None,
    ) -> dict[str, Any]:
        """Run ready jobs through an injected callback, or only schedule them."""

        campaign = self.get(campaign_id)
        self._refresh_ready(campaign)
        ready = list(self.next_ready(campaign_id))
        if executor is None:
            campaign.status = CampaignState.READY if ready else self._derived_campaign_state(campaign)
            self._emit(campaign, "ready", state=campaign.status.value, payload={"count": len(ready)})
            return self.dashboard(campaign_id)
        campaign.status = CampaignState.RUNNING
        self._emit(campaign, "started", state=campaign.status.value)
        limit = len(ready) if max_experiments is None else max(0, int(max_experiments))
        for experiment in ready[:limit]:
            self._run_one(campaign, experiment, executor)
            self._refresh_ready(campaign)
        campaign.status = self._derived_campaign_state(campaign)
        self._emit(campaign, "completed" if campaign.status == CampaignState.COMPLETED else "progress", state=campaign.status.value)
        self._persist(campaign)
        return self.dashboard(campaign_id)

    def pause(self, campaign_id: str) -> dict[str, Any]:
        campaign = self.get(campaign_id)
        if campaign.status not in {CampaignState.RUNNING, CampaignState.READY, CampaignState.QUEUED}:
            raise ValueError(f"cannot pause campaign in state {campaign.status.value}")
        campaign.status = CampaignState.PAUSED
        self._emit(campaign, "paused", state=campaign.status.value)
        self._persist(campaign)
        return self.dashboard(campaign_id)

    def resume(self, campaign_id: str) -> dict[str, Any]:
        campaign = self.get(campaign_id)
        if campaign.status != CampaignState.PAUSED:
            raise ValueError(f"cannot resume campaign in state {campaign.status.value}")
        campaign.status = CampaignState.QUEUED
        self._refresh_ready(campaign)
        self._emit(campaign, "resumed", state=campaign.status.value)
        self._persist(campaign)
        return self.dashboard(campaign_id)

    def cancel(self, campaign_id: str) -> dict[str, Any]:
        campaign = self.get(campaign_id)
        if campaign.status == CampaignState.COMPLETED:
            raise ValueError("completed campaign cannot be cancelled")
        for experiment in campaign.experiments:
            if experiment.state not in {CampaignState.COMPLETED, CampaignState.CANCELLED}:
                experiment.state = CampaignState.CANCELLED
        campaign.status = CampaignState.CANCELLED
        self._emit(campaign, "cancelled", state=campaign.status.value)
        self._persist(campaign)
        return self.dashboard(campaign_id)

    def retry(self, campaign_id: str, experiment_id: str | None = None) -> dict[str, Any]:
        campaign = self.get(campaign_id)
        selected = [item for item in campaign.experiments if experiment_id is None or item.experiment_id == experiment_id]
        if not selected:
            raise KeyError(f"unknown experiment_id: {experiment_id}")
        for experiment in selected:
            if experiment.state != CampaignState.FAILED:
                raise ValueError(f"experiment is not failed: {experiment.experiment_id}")
            experiment.state = CampaignState.RETRY
            experiment.error = None
            self._emit(campaign, "retry", experiment_id=experiment.experiment_id, state=experiment.state.value)
        campaign.status = CampaignState.QUEUED
        self._refresh_ready(campaign)
        self._persist(campaign)
        return self.dashboard(campaign_id)

    def dashboard(self, campaign_id: str) -> dict[str, Any]:
        campaign = self.get(campaign_id)
        counts = Counter(item.state.value for item in campaign.experiments)
        done = counts[CampaignState.COMPLETED.value]
        total = len(campaign.experiments)
        current = next((item.experiment_id for item in campaign.experiments if item.state == CampaignState.RUNNING), None)
        return {
            "campaign_id": campaign.campaign_id,
            "name": campaign.name,
            "status": campaign.status.value,
            "experiments_total": total,
            "experiments_completed": done,
            "progress": (done / total) if total else 0.0,
            "current_experiment": current,
            "eta": None,
            "validation_status": "pending",
            "generated_artifacts": self._artifact_paths(campaign),
            "state_counts": dict(sorted(counts.items())),
            "scientific_scope": CAMPAIGN_SCOPE,
        }

    def history(self, campaign_id: str) -> CampaignHistory:
        self.get(campaign_id)
        return self.histories[campaign_id]

    def manifest(self, campaign_id: str) -> CampaignManifest:
        campaign = self.get(campaign_id)
        output = self.output_dir(campaign)
        artifacts = [path for path in output.rglob("*") if path.is_file()] if output.exists() else []
        datasets = [Path(item) for item in campaign.datasets]
        return build_manifest(
            campaign,
            datasets=datasets,
            artifacts=artifacts,
            seeds=[int(item.config["seed"]) for item in campaign.experiments if "seed" in item.config],
            output_manifest=output / "manifest.json",
        )

    def validate(self, campaign_id: str) -> dict[str, Any]:
        """Collect existing validation fields; do not calculate new metrics."""

        campaign = self.get(campaign_id)
        rows: list[dict[str, Any]] = []
        missing = []
        for experiment in campaign.experiments:
            payload: Mapping[str, Any] = {}
            if experiment.result_path and Path(experiment.result_path).is_file():
                try:
                    loaded = json.loads(Path(experiment.result_path).read_text(encoding="utf-8"))
                    payload = loaded if isinstance(loaded, Mapping) else {}
                except (OSError, json.JSONDecodeError) as error:
                    rows.append({"experiment_id": experiment.experiment_id, "status": "invalid_json", "error": str(error)})
                    continue
            elif experiment.result_path:
                missing.append(experiment.experiment_id)
            validation = payload.get("validation", {})
            metrics = payload.get("metrics", {})
            rows.append(
                {
                    "experiment_id": experiment.experiment_id,
                    "state": experiment.state.value,
                    "result_path": experiment.result_path,
                    "overall_pass": validation.get("overall_pass", payload.get("overall_pass")),
                    "rmse": _existing_value(validation, metrics, "rmse"),
                    "mae": _existing_value(validation, metrics, "mae"),
                    "correlation": _existing_value(validation, metrics, "correlation"),
                    "effect_size": _existing_value(validation, metrics, "effect_size"),
                    "warnings": validation.get("warnings", payload.get("warnings", [])),
                    "outliers": validation.get("outliers", payload.get("outliers", [])),
                    "missing_data": validation.get("missing_data", payload.get("missing_data", [])),
                }
            )
        passed = not missing and all(row.get("overall_pass") is not False for row in rows)
        result = {
            "campaign_id": campaign_id,
            "overall_pass": passed,
            "experiment_count": len(rows),
            "missing_results": missing,
            "summaries": rows,
            "scientific_scope": CAMPAIGN_SCOPE,
        }
        output = self.output_dir(campaign) / "validation" / "validation_summary.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result

    def report(self, campaign_id: str, *, fmt: str = "json") -> Path:
        campaign = self.get(campaign_id)
        payload = {"campaign": campaign.as_dict(), "dashboard": self.dashboard(campaign_id), "validation": self.validate(campaign_id)}
        output = self.output_dir(campaign) / "reports"
        output.mkdir(parents=True, exist_ok=True)
        normalized = fmt.lower()
        if normalized == "json":
            path = output / "campaign_report.json"
            path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        elif normalized == "md":
            path = output / "campaign_report.md"
            path.write_text(_markdown_report(payload), encoding="utf-8")
        else:
            raise ValueError("report format must be json or md")
        return path

    def bundle(self, campaign_id: str, output_path: str | Path) -> Path:
        """Create a ZIP publication pack from existing campaign artifacts."""

        campaign = self.get(campaign_id)
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="research_campaign_") as temp:
            staging = Path(temp)
            for directory in ("validation", "figures", "tables", "reports", "publication", "checksums"):
                (staging / directory).mkdir()
            manifest = self.manifest(campaign_id).as_dict()
            (staging / "manifest.json").write_text(
                json.dumps({"campaign": campaign.as_dict(), "provenance": manifest}, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            source_root = self.output_dir(campaign)
            for directory in ("validation", "figures", "tables", "reports", "publication"):
                source = source_root / directory
                if source.exists():
                    for item in source.rglob("*"):
                        if item.is_file():
                            destination = staging / directory / item.relative_to(source)
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(item, destination)
            hashes = {
                path.relative_to(staging).as_posix(): file_sha256(path)
                for path in sorted(staging.rglob("*"))
                if path.is_file() and path.parent.name != "checksums"
            }
            (staging / "checksums" / "sha256.json").write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(staging.rglob("*")):
                    if path.is_dir():
                        archive.writestr(path.relative_to(staging).as_posix().rstrip("/") + "/", "")
                    else:
                        archive.write(path, path.relative_to(staging).as_posix())
        return target

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "root": self.root.as_posix(),
            "campaigns": [campaign.as_dict() for campaign in sorted(self.campaigns.values(), key=lambda item: item.campaign_id)],
            "histories": [history.as_dict() for history in self.histories.values()],
            "scientific_scope": CAMPAIGN_SCOPE,
        }
        target.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path, *, root: str | Path | None = None) -> "CampaignManager":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        manager = cls(root if root is not None else data.get("root", "campaigns"))
        for item in data.get("campaigns", ()):
            campaign = Campaign.from_dict(item)
            manager.campaigns[campaign.campaign_id] = campaign
        for item in data.get("histories", ()):
            history = CampaignHistory(str(item["campaign_id"]))
            history.extend(CampaignEvent.from_dict(event) for event in item.get("events", ()))
            manager.histories[history.campaign_id] = history
        for campaign_id in manager.campaigns:
            manager.histories.setdefault(campaign_id, CampaignHistory(campaign_id))
        return manager

    def output_dir(self, campaign: Campaign) -> Path:
        return self.root / campaign.campaign_id

    def _run_one(self, campaign: Campaign, experiment: ExperimentSpec, executor: Executor) -> None:
        experiment.state = CampaignState.RUNNING
        experiment.attempts += 1
        self._emit(campaign, "experiment_started", experiment_id=experiment.experiment_id, state=experiment.state.value)
        try:
            result = dict(executor(experiment))
            output = self.output_dir(campaign) / "reports" / f"{experiment.experiment_id}.json"
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            experiment.result_path = output.as_posix()
            experiment.state = CampaignState.COMPLETED
            self._emit(campaign, "experiment_completed", experiment_id=experiment.experiment_id, state=experiment.state.value)
        except Exception as error:  # caller-controlled stage failures are recorded, not hidden
            experiment.error = str(error)
            experiment.state = CampaignState.FAILED
            self._emit(campaign, "experiment_failed", experiment_id=experiment.experiment_id, state=experiment.state.value, payload={"error": str(error)})

    def _refresh_ready(self, campaign: Campaign) -> None:
        by_id = {item.experiment_id: item for item in campaign.experiments}
        for experiment in campaign.experiments:
            if experiment.state not in {CampaignState.QUEUED, CampaignState.RETRY}:
                continue
            if all(by_id[dependency].state == CampaignState.COMPLETED for dependency in experiment.dependencies):
                experiment.state = CampaignState.READY

    def _validate_dependencies(self, campaign: Campaign) -> None:
        known = {item.experiment_id for item in campaign.experiments}
        for experiment in campaign.experiments:
            missing = set(experiment.dependencies) - known
            if missing:
                raise ValueError(f"unknown dependencies for {experiment.experiment_id}: {sorted(missing)}")

    def _derived_campaign_state(self, campaign: Campaign) -> CampaignState:
        states = {item.state for item in campaign.experiments}
        if states and states <= {CampaignState.COMPLETED}:
            return CampaignState.COMPLETED
        if CampaignState.PAUSED in states:
            return CampaignState.PAUSED
        if states and states <= {CampaignState.CANCELLED, CampaignState.COMPLETED}:
            return CampaignState.CANCELLED
        if CampaignState.FAILED in states:
            return CampaignState.FAILED
        if CampaignState.READY in states:
            return CampaignState.READY
        return CampaignState.QUEUED

    def _emit(self, campaign: Campaign, event_type: str, *, experiment_id: str | None = None, state: str | None = None, payload: Mapping[str, Any] | None = None) -> None:
        self.histories.setdefault(campaign.campaign_id, CampaignHistory(campaign.campaign_id)).append(
            CampaignEvent(
                event_type=event_type,
                campaign_id=campaign.campaign_id,
                experiment_id=experiment_id,
                state=state,
                author=campaign.author,
                payload=dict(payload or {}),
            )
        )

    def _persist(self, campaign: Campaign) -> None:
        output = self.output_dir(campaign)
        output.mkdir(parents=True, exist_ok=True)
        campaign.save(output / "campaign.json")
        self.history(campaign.campaign_id).save(output / "history.json")

    def _artifact_paths(self, campaign: Campaign) -> list[str]:
        output = self.output_dir(campaign)
        return [path.relative_to(output).as_posix() for path in sorted(output.rglob("*")) if path.is_file()] if output.exists() else []


def _existing_value(validation: Mapping[str, Any], metrics: Mapping[str, Any], key: str) -> Any:
    return validation.get(key, metrics.get(key))


def _jsonable(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


def _markdown_report(payload: Mapping[str, Any]) -> str:
    dashboard = payload["dashboard"]
    validation = payload["validation"]
    return "\n".join(
        [
            f"# Campaign Report: {dashboard['name']}",
            "",
            f"- Status: `{dashboard['status']}`",
            f"- Progress: `{dashboard['experiments_completed']}/{dashboard['experiments_total']}`",
            f"- Validation pass: `{validation['overall_pass']}`",
            "",
            "This is a computational orchestration report. It does not run simulations or establish biological validation.",
            "",
        ]
    )


__all__ = ["CampaignManager", "Executor"]
