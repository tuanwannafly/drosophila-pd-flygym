"""Scientific Operating System kernel for existing research subsystems."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from drosophila_pd.dataset_adapter import discover_datasets
from drosophila_pd.experiment_runtime import ExperimentContext, ExperimentRuntime
from drosophila_pd.research_campaign import Campaign
from drosophila_pd.research_pipeline import StudyOrchestrator

from .kernel_context import KernelContext
from .kernel_events import KernelEventType, ResearchBus
from .kernel_registry import ResourceManager, ServiceRegistry
from .kernel_scheduler import TaskResult, TaskScheduler
from .kernel_state import KernelState


class ResearchKernel:
    """Coordinate the existing adapter, runtime, campaign, and study APIs."""

    def __init__(self, context: KernelContext) -> None:
        self.context = context
        self.state = self._load_state()
        self.bus = self._load_bus()
        self.registry = ServiceRegistry()
        self.resources = self._load_resources()
        self.runtime: ExperimentRuntime | None = None
        self.scheduler = TaskScheduler(self.bus)
        self._configure_services()

    def boot(self) -> dict[str, Any]:
        """Boot and run the dependency graph until it completes or must wait."""

        self.state = KernelState.BOOTING
        self.bus.publish(KernelEventType.KERNEL_BOOTED, "Research Kernel booted.", context=self.context.as_dict())
        self._ensure_runtime()
        self._configure_tasks()
        self.state = KernelState.RUNNING
        results = self.scheduler.run_all()
        self._sync_runtime_events()
        self._refresh_resources()
        if any(item.status == "FAILED" for item in results):
            self.state = KernelState.FAILED
        elif any(item.status == "WAITING_DATASET" for item in results):
            self.state = KernelState.WAITING_DATASET
            self.bus.publish(KernelEventType.WAITING_DATASET, "Kernel is waiting for a ready dataset.")
        else:
            self.state = KernelState.READY
            self.bus.publish(KernelEventType.KERNEL_READY, "Research Kernel is ready.")
        self._persist()
        return self.as_dict()

    def status(self) -> dict[str, Any]:
        self._refresh_resources()
        self._persist()
        return self.as_dict()

    def resource_report(self) -> dict[str, Any]:
        self._refresh_resources()
        self.resources.save(self.context.resources_path)
        return self.resources.as_dict()

    def event_report(self) -> dict[str, Any]:
        return self.bus.as_dict()

    def shutdown(self) -> dict[str, Any]:
        self.state = KernelState.SHUTDOWN
        self.bus.publish(KernelEventType.KERNEL_SHUTDOWN, "Research Kernel shut down.")
        self._persist()
        return self.as_dict()

    def as_dict(self) -> dict[str, Any]:
        return {
            "kernel_schema_version": 1,
            "state": self.state.value,
            "context": self.context.as_dict(),
            "tasks": [item.as_dict() for item in self.scheduler.results()],
            "resources": self.resources.as_dict(),
            "services": self.registry.as_dict(),
            "event_count": len(self.bus.records()),
            "scientific_scope": "Orchestration only; no simulation or scientific computation.",
        }

    def _configure_services(self) -> None:
        self.registry.register(
            "dataset_adapter",
            discover_datasets,
            module="drosophila_pd.dataset_adapter",
            metadata={"role": "read-only dataset discovery"},
        )
        self.registry.register(
            "experiment_runtime",
            self.runtime,
            module="drosophila_pd.experiment_runtime",
            available=False,
            metadata={"role": "session orchestration"},
        )
        self.registry.register("campaign", Campaign, module="drosophila_pd.research_campaign", metadata={"role": "existing campaign API"})
        self.registry.register("study", StudyOrchestrator, module="drosophila_pd.research_pipeline", metadata={"role": "existing study API"})
        for name, module in (
            ("digital_twin", "drosophila_pd.digital_twin"),
            ("analysis", "drosophila_pd.analysis"),
            ("statistics", "drosophila_pd.statistics"),
            ("pd", "drosophila_pd.computational_pd"),
            ("validation", "drosophila_pd.scientific_validation"),
            ("publication", "drosophila_pd.publication"),
        ):
            self.registry.register(name, module=module, available=False, metadata={"reason": "No binding in V9; existing API remains authoritative."})

    def _configure_tasks(self) -> None:
        if self.runtime is None:
            raise RuntimeError("Experiment runtime has not been initialized")
        self.scheduler.register("prepare", self.runtime.prepare)
        self.scheduler.register("bind", self.runtime.bind, dependencies=("prepare",))
        self.scheduler.register("run", self._run, dependencies=("bind",))
        self.scheduler.register("validate", self.runtime.summary, dependencies=("run",))
        self.scheduler.register("package", self.runtime.summary, dependencies=("validate",))
        self.scheduler.register("archive", self.runtime.archive, dependencies=("package",))

    def _run(self) -> dict[str, Any]:
        self.bus.publish(KernelEventType.CAMPAIGN_STARTED, "Existing campaign orchestration started.")
        return self.runtime.run()

    def _ensure_runtime(self) -> None:
        if self.runtime is None:
            self.runtime = ExperimentRuntime(
                ExperimentContext(
                    self.context.repository_root,
                    experiment_id=self.context.experiment_id,
                    output_root=self.context.experiment_root,
                )
            )
            self.registry.register(
                "experiment_runtime",
                self.runtime,
                module="drosophila_pd.experiment_runtime",
                available=True,
                metadata={"role": "session orchestration"},
            )

    def _sync_runtime_events(self) -> None:
        if self.runtime is None:
            return
        existing = {(event.event, event.timestamp) for event in self.bus.records()}
        for event in self.runtime.events.events:
            event_name = event.event.value
            if (event_name, event.timestamp) not in existing:
                self.bus.publish(event_name, event.message, **dict(event.payload))
        if any(item.status == "COMPLETED" and item.name == "run" for item in self.scheduler.results()):
            self.bus.publish(KernelEventType.STUDY_COMPLETED, "Existing study orchestration completed.")
            self.bus.publish(KernelEventType.PACKAGE_CREATED, "Existing research package is available.")
        if any(item.status == "COMPLETED" and item.name == "archive" for item in self.scheduler.results()):
            self.bus.publish(KernelEventType.ARCHIVED, "Research output archive is available.")

    def _refresh_resources(self) -> None:
        if self.runtime is not None:
            discovery = self.runtime.discovery or self.runtime.discover()
            for dataset in discovery.datasets:
                self.resources.register("datasets", dataset.root, metadata={"dataset_id": dataset.dataset_id})
            for missing_type in discovery.missing_types:
                self.resources.register_missing("datasets", self.context.repository_root / "datasets" / missing_type, metadata={"dataset_type": missing_type})
            root = self.context.experiment_root
            if root.is_dir():
                for path in root.rglob("*"):
                    if not path.is_file():
                        continue
                    category = _resource_category(path)
                    self.resources.register(category, path)

    def _persist(self) -> None:
        self.context.output_root.mkdir(parents=True, exist_ok=True)
        self.bus.save(self.context.events_path)
        timeline = {
            "timeline_schema_version": 1,
            "events": [
                {"index": index, **event.as_dict()}
                for index, event in enumerate(self.bus.records())
            ],
        }
        self.context.timeline_path.write_text(json.dumps(timeline, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.context.state_path.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.registry.save(self.context.registry_path)
        self.resources.save(self.context.resources_path)
        lines = [f"{event.timestamp} {event.event} {event.message}" for event in self.bus.records()]
        self.context.kernel_log.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def _load_bus(self) -> ResearchBus:
        return ResearchBus.load(self.context.events_path) if self.context.events_path.is_file() else ResearchBus()

    def _load_state(self) -> KernelState:
        if not self.context.state_path.is_file():
            return KernelState.STOPPED
        try:
            return KernelState(str(json.loads(self.context.state_path.read_text(encoding="utf-8")).get("state", KernelState.STOPPED)))
        except (OSError, ValueError):
            return KernelState.STOPPED

    def _load_resources(self) -> ResourceManager:
        manager = ResourceManager()
        if not self.context.resources_path.is_file():
            return manager
        try:
            payload = json.loads(self.context.resources_path.read_text(encoding="utf-8"))
            for item in payload.get("resources", ()):
                if item.get("exists", True):
                    manager.register(item["category"], item["path"], metadata=item.get("metadata", {}))
                else:
                    manager.register_missing(item["category"], item["path"], metadata=item.get("metadata", {}))
        except (OSError, ValueError, KeyError):
            return ResourceManager()
        return manager


def _resource_category(path: Path) -> str:
    name = path.name.lower()
    parts = {part.lower() for part in path.parts}
    if name.endswith((".zip", ".tar", ".tar.gz")) or "bundle" in name or "package" in name:
        return "bundles"
    for category in ("reports", "figures", "tables", "artifacts"):
        if category in parts or category.rstrip("s") in name:
            return category
    if name in {"session.json", "execution.json", "runtime_state.json"}:
        return "sessions"
    return "artifacts"


__all__ = ["ResearchKernel"]
