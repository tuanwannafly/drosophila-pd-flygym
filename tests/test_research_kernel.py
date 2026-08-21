"""Tests for V9 orchestration only; no rollout or simulation data is created."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from drosophila_pd.research_kernel import (
    KernelContext,
    KernelEventType,
    KernelState,
    ResearchBus,
    ResearchKernel,
    ServiceRegistry,
    TaskScheduler,
)


def test_event_bus_publish_subscribe_and_persistence(tmp_path: Path) -> None:
    received: list[str] = []
    bus = ResearchBus()
    bus.subscribe(lambda event: received.append(event.event), KernelEventType.DATASET_READY)
    bus.publish(KernelEventType.DATASET_READY, "ready", dataset_id="fixture")

    path = bus.save(tmp_path / "events.json")
    restored = ResearchBus.load(path)

    assert received == [KernelEventType.DATASET_READY]
    assert restored.records()[0].payload["dataset_id"] == "fixture"


def test_registry_tracks_available_and_unavailable_services() -> None:
    registry = ServiceRegistry()
    registry.register("available", object(), module="example")
    registry.register("future", module="future.module", available=False)

    assert registry.get("available") is not None
    assert registry.record("future").available is False
    assert registry.as_dict()["services"][1]["module"] == "future.module"


def test_scheduler_respects_dependencies_and_waiting_state() -> None:
    calls: list[str] = []
    scheduler = TaskScheduler()
    scheduler.register("prepare", lambda: calls.append("prepare") or {"state": "WAITING_DATASET"})
    scheduler.register("run", lambda: calls.append("run"), dependencies=("prepare",))

    results = scheduler.run_all()

    assert calls == ["prepare"]
    assert [item.status for item in results] == ["WAITING_DATASET"]


def test_kernel_waits_without_dataset_and_persists_operational_outputs(tmp_path: Path) -> None:
    context = KernelContext(tmp_path, output_root=tmp_path / "kernel")
    kernel = ResearchKernel(context)
    report = kernel.boot()

    assert report["state"] == KernelState.WAITING_DATASET.value
    assert report["event_count"] > 0
    assert report["services"]["services"]
    assert (context.output_root / "kernel.log").is_file()
    assert (context.output_root / "events.json").is_file()
    assert (context.output_root / "timeline.json").is_file()
    assert (context.output_root / "resources.json").is_file()
    assert (context.output_root / "registry.json").is_file()
    assert (context.output_root / "kernel_state.json").is_file()
    assert any(event["event"] == KernelEventType.WAITING_DATASET for event in json.loads((context.output_root / "events.json").read_text())["events"])


def test_kernel_cli_status_and_shutdown(tmp_path: Path) -> None:
    script = Path(__file__).resolve().parents[1] / "scripts" / "kernel.py"
    output = tmp_path / "kernel"
    boot = subprocess.run(
        [sys.executable, str(script), "boot", "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(boot.stdout)["state"] == KernelState.WAITING_DATASET.value

    status = subprocess.run(
        [sys.executable, str(script), "status", "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(status.stdout)["state"] == KernelState.WAITING_DATASET.value

    shutdown = subprocess.run(
        [sys.executable, str(script), "shutdown", "--output", str(output)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(shutdown.stdout)["state"] == KernelState.SHUTDOWN.value
