"""Campaign creation, state transitions, progress, and planning reports."""

from __future__ import annotations

import csv
import hashlib
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

import yaml

from .models import (
    CAMPAIGN_SCOPE,
    Campaign,
    CampaignHistory,
    CampaignManifest,
    CampaignProgress,
    CampaignStatus,
    CampaignSummary,
    current_provenance,
)


TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.PLANNED: frozenset({CampaignStatus.READY, CampaignStatus.WAITING_DATASET, CampaignStatus.ARCHIVED}),
    CampaignStatus.WAITING_DATASET: frozenset({CampaignStatus.READY, CampaignStatus.ARCHIVED}),
    CampaignStatus.READY: frozenset({CampaignStatus.QUEUED, CampaignStatus.WAITING_DATASET, CampaignStatus.ARCHIVED}),
    CampaignStatus.QUEUED: frozenset({CampaignStatus.RUNNING, CampaignStatus.PAUSED, CampaignStatus.FAILED, CampaignStatus.ARCHIVED}),
    CampaignStatus.RUNNING: frozenset({CampaignStatus.PAUSED, CampaignStatus.FAILED, CampaignStatus.COMPLETED}),
    CampaignStatus.PAUSED: frozenset({CampaignStatus.QUEUED, CampaignStatus.RUNNING, CampaignStatus.FAILED}),
    CampaignStatus.FAILED: frozenset({CampaignStatus.QUEUED, CampaignStatus.ARCHIVED}),
    CampaignStatus.COMPLETED: frozenset({CampaignStatus.ARCHIVED}),
    CampaignStatus.ARCHIVED: frozenset(),
}


class CampaignManager:
    """Manage campaign plans without executing experiments."""

    def __init__(self, root: str | Path = "campaigns") -> None:
        self.root = Path(root)
        self.campaigns: dict[str, Campaign] = {}
        self.histories: dict[str, CampaignHistory] = {}

    def create(self, campaign: Campaign, *, expand: bool = True) -> Campaign:
        if campaign.campaign_id in self.campaigns:
            raise ValueError(f"duplicate campaign_id: {campaign.campaign_id}")
        if expand and not campaign.matrix:
            campaign.matrix = self.expand_matrix_definition(campaign.metadata.get("matrix", {}), campaign.campaign_id, campaign.expected_outputs)
        self.campaigns[campaign.campaign_id] = campaign
        self.histories[campaign.campaign_id] = CampaignHistory(campaign.campaign_id)
        self.histories[campaign.campaign_id].append("created", status=campaign.status, payload={"name": campaign.name})
        return campaign

    def create_from_template(
        self,
        template: str | Path | Mapping[str, Any],
        *,
        campaign_id: str | None = None,
        datasets: Sequence[str] = (),
    ) -> Campaign:
        payload = self._read_template(template)
        campaign_kwargs: dict[str, Any] = {
            "name": str(payload.get("name", payload.get("campaign_type", "campaign"))),
            "campaign_type": str(payload.get("campaign_type", "custom")),
            "description": str(payload.get("description", "")),
            "author": str(payload.get("author", "")),
            "datasets": list(datasets or payload.get("datasets", ())),
            "expected_outputs": [str(item) for item in payload.get("expected_outputs", ())],
            "priority": int(payload.get("priority", 0)),
            "metadata": dict(payload),
        }
        selected_id = campaign_id or payload.get("campaign_id")
        if selected_id:
            campaign_kwargs["campaign_id"] = str(selected_id)
        campaign = Campaign(**campaign_kwargs)
        return self.create(campaign)

    def get(self, campaign_id: str) -> Campaign:
        try:
            return self.campaigns[campaign_id]
        except KeyError as error:
            raise KeyError(f"unknown campaign_id: {campaign_id}") from error

    def transition(self, campaign_id: str, status: CampaignStatus | str, *, reason: str = "") -> Campaign:
        campaign = self.get(campaign_id)
        target = status if isinstance(status, CampaignStatus) else CampaignStatus(str(status).upper())
        if target != campaign.status and target not in TRANSITIONS[campaign.status]:
            raise ValueError(f"invalid campaign transition: {campaign.status.value} -> {target.value}")
        campaign.status = target
        campaign.touch()
        self.histories[campaign_id].append("state_changed", status=target, payload={"reason": reason})
        return campaign

    def set_dataset_available(self, campaign_id: str, available: bool) -> Campaign:
        target = CampaignStatus.READY if available else CampaignStatus.WAITING_DATASET
        return self.transition(campaign_id, target, reason="dataset gate")

    def record_experiment(self, campaign_id: str, experiment_id: str, status: CampaignStatus | str, **updates: Any) -> dict[str, Any]:
        campaign = self.get(campaign_id)
        target = status if isinstance(status, CampaignStatus) else CampaignStatus(str(status).upper())
        for row in campaign.matrix:
            if row.get("experiment_id") == experiment_id:
                row["status"] = target.value
                row.update(updates)
                campaign.touch()
                self.histories[campaign_id].append("experiment_updated", status=target, payload={"experiment_id": experiment_id, **updates})
                return row
        raise KeyError(f"unknown experiment_id: {experiment_id}")

    def progress(self, campaign_id: str) -> CampaignProgress:
        campaign = self.get(campaign_id)
        counts = Counter(str(row.get("status", CampaignStatus.PLANNED.value)).upper() for row in campaign.matrix)
        output_root = self.root / campaign.campaign_id
        files = [path for path in output_root.rglob("*") if path.is_file()] if output_root.is_dir() else []
        runtime = sum(float(row.get("duration", 0.0) or 0.0) for row in campaign.matrix if _number(row.get("duration")) is not None)
        validation = str(campaign.metadata.get("validation_status", "PENDING"))
        publication = str(campaign.metadata.get("publication_readiness", "PLANNING_ONLY"))
        return CampaignProgress(
            total=len(campaign.matrix),
            completed=counts[CampaignStatus.COMPLETED.value],
            failed=counts[CampaignStatus.FAILED.value],
            waiting=counts[CampaignStatus.WAITING_DATASET.value] + (len(campaign.matrix) if campaign.status == CampaignStatus.WAITING_DATASET else 0),
            queued=counts[CampaignStatus.QUEUED.value],
            running=counts[CampaignStatus.RUNNING.value],
            runtime_estimate_s=runtime if runtime else None,
            storage_bytes=sum(path.stat().st_size for path in files),
            artifact_count=len(files),
            validation_status=validation,
            publication_readiness=publication,
        )

    def summary(self, campaign_id: str) -> CampaignSummary:
        campaign = self.get(campaign_id)
        return CampaignSummary(campaign.campaign_id, campaign.name, campaign.status, self.progress(campaign_id), tuple(campaign.datasets), tuple(campaign.expected_outputs))

    def manifest(self, campaign_id: str) -> CampaignManifest:
        campaign = self.get(campaign_id)
        artifact_hashes: dict[str, str] = {}
        output_root = self.root / campaign.campaign_id
        if output_root.is_dir():
            for path in sorted(output_root.rglob("*")):
                if path.is_file():
                    artifact_hashes[path.relative_to(output_root).as_posix()] = _sha256(path)
        return current_provenance(campaign, artifacts=artifact_hashes)

    def write_dashboard(self, campaign_id: str, output: str | Path | None = None) -> dict[str, Path]:
        campaign = self.get(campaign_id)
        target = Path(output) if output is not None else self.root / campaign_id / "dashboard"
        target.mkdir(parents=True, exist_ok=True)
        summary = self.summary(campaign_id)
        paths = {
            "summary": target / "campaign_summary.json",
            "status": target / "campaign_status.csv",
            "progress": target / "campaign_progress.md",
            "health": target / "campaign_health.json",
            "inventory": target / "campaign_inventory.csv",
        }
        paths["summary"].write_text(json.dumps(summary.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with paths["status"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("experiment_id", "status", "dataset", "seed", "priority", "expected_outputs"))
            writer.writeheader()
            for row in campaign.matrix:
                writer.writerow({field: row.get(field, "") for field in writer.fieldnames})
        progress = summary.progress
        paths["progress"].write_text(
            f"# Campaign Progress: {campaign.name}\n\n"
            f"- Status: `{campaign.status.value}`\n"
            f"- Completed: `{progress.completed}/{progress.total}`\n"
            f"- Failed: `{progress.failed}`\n"
            f"- Waiting for dataset: `{progress.waiting}`\n"
            f"- Runtime estimate (planning): `{progress.runtime_estimate_s}` seconds\n\n"
            "This is an orchestration report. No simulation was run.\n",
            encoding="utf-8",
        )
        health = {
            "campaign_id": campaign_id,
            "status": campaign.status.value,
            "dataset_gate": "READY" if campaign.status not in {CampaignStatus.WAITING_DATASET, CampaignStatus.PLANNED} else "WAITING_DATASET",
            "failed_experiments": progress.failed,
            "validation_status": progress.validation_status,
            "publication_readiness": progress.publication_readiness,
            "overall_pass": progress.failed == 0 and campaign.status not in {CampaignStatus.PLANNED, CampaignStatus.WAITING_DATASET, CampaignStatus.FAILED},
            "scientific_scope": CAMPAIGN_SCOPE,
        }
        paths["health"].write_text(json.dumps(health, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        with paths["inventory"].open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=("experiment_id", "expected_output", "status"))
            writer.writeheader()
            for row in campaign.matrix:
                for artifact in row.get("expected_outputs", campaign.expected_outputs):
                    writer.writerow({"experiment_id": row.get("experiment_id", ""), "expected_output": artifact, "status": row.get("status", CampaignStatus.PLANNED.value)})
        return paths

    def write_publication_plan(self, campaign_id: str, output: str | Path | None = None) -> dict[str, Path]:
        campaign = self.get(campaign_id)
        target = Path(output) if output is not None else self.root / campaign_id / "publication"
        target.mkdir(parents=True, exist_ok=True)
        paths = {
            "figures": target / "figure_plan.md",
            "tables": target / "table_plan.md",
            "mapping": target / "experiment_mapping.csv",
            "supplement": target / "supplement_mapping.csv",
            "reviewer": target / "reviewer_checklist.md",
            "readiness": target / "publication_readiness.md",
        }
        paths["figures"].write_text("# Figure Plan\n\nPlanning targets only; no figures are generated by the campaign manager.\n\n- Trajectory overview\n- Speed and body summaries\n- Validation/provenance overview\n", encoding="utf-8")
        paths["tables"].write_text("# Table Plan\n\nPlanning targets only; no result tables are generated.\n\n- Dataset summary\n- Experiment status\n- Validation and reproducibility\n", encoding="utf-8")
        for key, field in (("mapping", "experiment_id"), ("supplement", "experiment_id")):
            with paths[key].open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=(field, "source", "status"))
                writer.writeheader()
                for row in campaign.matrix:
                    writer.writerow({field: row.get(field, ""), "source": "existing pipeline; pending dataset", "status": "PLANNED"})
        paths["reviewer"].write_text("# Reviewer Checklist\n\n- [ ] Dataset manifest and checksums verified.\n- [ ] All planned experiments accounted for.\n- [ ] Validation and provenance complete.\n- [ ] Scientific scope remains computational only.\n", encoding="utf-8")
        paths["readiness"].write_text("# Publication Readiness\n\nStatus: `PLANNING_ONLY`\n\nNo figures, tables, results, or biological conclusions are generated by this planning layer.\n", encoding="utf-8")
        return paths

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "root": self.root.as_posix(),
            "campaigns": [campaign.as_dict() for campaign in self.campaigns.values()],
            "histories": [history.as_dict() for history in self.histories.values()],
            "scientific_scope": CAMPAIGN_SCOPE,
        }
        target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target

    @classmethod
    def load(cls, path: str | Path, *, root: str | Path | None = None) -> "CampaignManager":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        manager = cls(root if root is not None else payload.get("root", "campaigns"))
        for item in payload.get("campaigns", ()):
            campaign = Campaign.from_dict(item)
            manager.campaigns[campaign.campaign_id] = campaign
        for item in payload.get("histories", ()):
            history = CampaignHistory(str(item["campaign_id"]), list(item.get("events", ())))
            manager.histories[history.campaign_id] = history
        for campaign_id in manager.campaigns:
            manager.histories.setdefault(campaign_id, CampaignHistory(campaign_id))
        return manager

    @staticmethod
    def expand_matrix_definition(definition: Mapping[str, Any], campaign_id: str, expected_outputs: Sequence[str]) -> list[dict[str, Any]]:
        """Expand only declarative dimensions; no executor is invoked."""

        definition = dict(definition or {})
        def values(name: str, fallback: Any) -> list[Any]:
            value = definition.get(name, fallback)
            if isinstance(value, (list, tuple)):
                return list(value)
            return [value]

        datasets = values("dataset", definition.get("datasets", ["PENDING_DATASET"]))
        seeds = values("seed", definition.get("seeds", [0]))
        controllers = values("controller", definition.get("controllers", ["PENDING_CONTROLLER"]))
        terrains = values("terrain", definition.get("terrains", ["PENDING_TERRAIN"]))
        noise = values("noise", [False])
        perturbations = values("perturbation", definition.get("perturbations", ["none"]))
        durations = values("duration", definition.get("durations", [0.0]))
        replicates = max(1, int(definition.get("replicates", 1)))
        priority = int(definition.get("priority", 0))
        rows: list[dict[str, Any]] = []
        dimensions = itertools.product(datasets, seeds, controllers, terrains, noise, perturbations, durations)
        for index, (dataset, seed, controller, terrain, noise_value, perturbation, duration) in enumerate(dimensions, start=1):
            for replicate in range(1, replicates + 1):
                rows.append({
                    "experiment_id": f"{campaign_id}_{index:04d}_r{replicate:02d}",
                    "dataset": dataset,
                    "seed": int(seed),
                    "controller": controller,
                    "terrain": terrain,
                    "noise": noise_value,
                    "perturbation": perturbation,
                    "duration": duration,
                    "replicate": replicate,
                    "priority": priority,
                    "expected_outputs": list(expected_outputs),
                    "status": CampaignStatus.PLANNED.value,
                })
        return rows

    @staticmethod
    def _read_template(template: str | Path | Mapping[str, Any]) -> Mapping[str, Any]:
        if isinstance(template, Mapping):
            return template
        path = Path(template)
        with path.open(encoding="utf-8") as handle:
            value = yaml.safe_load(handle)
        if not isinstance(value, Mapping):
            raise ValueError(f"campaign template must be a mapping: {path}")
        return value


def _number(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = ["CampaignManager", "TRANSITIONS"]
