"""Research campaign planning and resumable orchestration for v2.

The campaign layer is an additive orchestration framework. It plans and
organizes computational experiments, but it does not import FlyGym, run MuJoCo,
change controllers, or create perturbations. Simulation execution is supplied
by callers through an explicit executor function.
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.campaign_provenance import stable_hash


CAMPAIGN_SCOPE = (
    "Version 2 computational campaign orchestration only; no biological "
    "validation, diagnosis, disease-severity mapping, or mechanistic claim."
)


@dataclass(frozen=True)
class CampaignConfig:
    """Deterministic configuration for a research campaign."""

    campaign_id: str
    roles: tuple[str, ...] = ("Healthy", "Candidate")
    progression_stages: tuple[str, ...] = ()
    interventions: tuple[str, ...] = ()
    custom_scenarios: tuple[str, ...] = ()
    parameter_grid: Mapping[str, Sequence[Any]] = field(default_factory=dict)
    seeds: tuple[int, ...] = (0,)
    replicates: int = 1
    metadata: Mapping[str, Any] = field(default_factory=dict)
    version: str = "v2.campaign.1"

    def __post_init__(self) -> None:
        if not self.campaign_id:
            raise ValueError("campaign_id is required.")
        if self.replicates <= 0:
            raise ValueError("replicates must be positive.")
        if not self.seeds:
            raise ValueError("at least one seed is required.")
        for seed in self.seeds:
            if int(seed) != seed:
                raise ValueError("seeds must be integers.")

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "version": self.version,
            "scientific_scope": CAMPAIGN_SCOPE,
            "roles": list(self.roles),
            "progression_stages": list(self.progression_stages),
            "interventions": list(self.interventions),
            "custom_scenarios": list(self.custom_scenarios),
            "parameter_grid": {key: list(value) for key, value in sorted(self.parameter_grid.items())},
            "seeds": [int(seed) for seed in self.seeds],
            "replicates": int(self.replicates),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CampaignConfig":
        return cls(
            campaign_id=str(data["campaign_id"]),
            roles=tuple(data.get("roles", ("Healthy", "Candidate"))),
            progression_stages=tuple(data.get("progression_stages", ())),
            interventions=tuple(data.get("interventions", ())),
            custom_scenarios=tuple(data.get("custom_scenarios", ())),
            parameter_grid=dict(data.get("parameter_grid", {})),
            seeds=tuple(int(seed) for seed in data.get("seeds", (0,))),
            replicates=int(data.get("replicates", 1)),
            metadata=dict(data.get("metadata", {})),
            version=str(data.get("version", "v2.campaign.1")),
        )


@dataclass(frozen=True)
class ExperimentPlan:
    """One planned campaign experiment."""

    experiment_id: str
    campaign_id: str
    role: str
    seed: int
    replicate: int
    parameters: Mapping[str, Any] = field(default_factory=dict)
    progression_stage: str | None = None
    intervention: str | None = None
    scenario: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "campaign_id": self.campaign_id,
            "role": self.role,
            "seed": int(self.seed),
            "replicate": int(self.replicate),
            "parameters": dict(sorted(self.parameters.items())),
            "progression_stage": self.progression_stage,
            "intervention": self.intervention,
            "scenario": self.scenario,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CampaignManifest:
    """Manifest for the planned campaign matrix."""

    campaign_id: str
    config_hash: str
    experiment_count: int
    experiment_ids: tuple[str, ...]
    created_at: str
    scientific_scope: str = CAMPAIGN_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "config_hash": self.config_hash,
            "experiment_count": int(self.experiment_count),
            "experiment_ids": list(self.experiment_ids),
            "created_at": self.created_at,
            "scientific_scope": self.scientific_scope,
        }


@dataclass(frozen=True)
class CampaignCheckpoint:
    """Resumable execution checkpoint."""

    campaign_id: str
    completed_ids: tuple[str, ...] = ()
    failed_ids: tuple[str, ...] = ()
    output_refs: Mapping[str, str] = field(default_factory=dict)
    cursor: int = 0
    checkpoint_hash: str = ""

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "campaign_id": self.campaign_id,
            "completed_ids": list(self.completed_ids),
            "failed_ids": list(self.failed_ids),
            "output_refs": dict(sorted(self.output_refs.items())),
            "cursor": int(self.cursor),
        }
        return {**payload, "checkpoint_hash": self.checkpoint_hash or stable_hash(payload)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "CampaignCheckpoint":
        return cls(
            campaign_id=str(data["campaign_id"]),
            completed_ids=tuple(data.get("completed_ids", ())),
            failed_ids=tuple(data.get("failed_ids", ())),
            output_refs=dict(data.get("output_refs", {})),
            cursor=int(data.get("cursor", 0)),
            checkpoint_hash=str(data.get("checkpoint_hash", "")),
        )


@dataclass(frozen=True)
class CampaignHistory:
    """Execution history for completed and failed campaign experiments."""

    campaign_id: str
    events: tuple[Mapping[str, Any], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {"campaign_id": self.campaign_id, "events": [dict(event) for event in self.events]}


@dataclass(frozen=True)
class Campaign:
    """Planned campaign with deterministic matrix and manifest."""

    config: CampaignConfig
    experiments: tuple[ExperimentPlan, ...]
    manifest: CampaignManifest

    def as_dict(self) -> dict[str, Any]:
        return {
            "config": self.config.as_dict(),
            "manifest": self.manifest.as_dict(),
            "experiments": [experiment.as_dict() for experiment in self.experiments],
        }


@dataclass(frozen=True)
class CampaignResume:
    """Resume decision for a partially completed campaign."""

    remaining: tuple[ExperimentPlan, ...]
    checkpoint: CampaignCheckpoint


class CampaignScheduler:
    """Build deterministic experiment schedules from campaign configs."""

    def schedule(self, config: CampaignConfig) -> tuple[ExperimentPlan, ...]:
        return generate_experiment_matrix(config)


class CampaignRunner:
    """Run campaign plans through a caller-supplied executor."""

    def run(
        self,
        campaign: Campaign,
        executor: Callable[[ExperimentPlan], Mapping[str, Any]],
        *,
        output_dir: str | Path | None = None,
        checkpoint: CampaignCheckpoint | None = None,
        max_experiments: int | None = None,
    ) -> tuple[CampaignHistory, CampaignCheckpoint]:
        output = Path(output_dir) if output_dir is not None else None
        if output is not None:
            (output / "logs").mkdir(parents=True, exist_ok=True)
            (output / "reports").mkdir(parents=True, exist_ok=True)
        completed = list(checkpoint.completed_ids if checkpoint else ())
        failed = list(checkpoint.failed_ids if checkpoint else ())
        output_refs = dict(checkpoint.output_refs if checkpoint else {})
        skip = set(completed) | set(failed)
        events: list[Mapping[str, Any]] = []
        remaining = [plan for plan in campaign.experiments if plan.experiment_id not in skip]
        if max_experiments is not None:
            remaining = remaining[: max(0, int(max_experiments))]
        for index, plan in enumerate(remaining, start=1):
            started = utc_timestamp()
            try:
                result = dict(executor(plan))
                if output is not None:
                    report_path = output / "reports" / f"{plan.experiment_id}.json"
                    report_path.write_text(
                        json.dumps(_jsonable(result), indent=2, sort_keys=True),
                        encoding="utf-8",
                    )
                    output_refs[plan.experiment_id] = str(report_path)
                completed.append(plan.experiment_id)
                event = _event(plan, "completed", started, result)
            except Exception as exc:  # pragma: no cover - tested through public failure path
                failed.append(plan.experiment_id)
                event = _event(plan, "failed", started, {"error": str(exc)})
            events.append(event)
            if output is not None:
                _append_jsonl(output / "logs" / "campaign_log.jsonl", event)
                checkpoint_payload = CampaignCheckpoint(
                    campaign_id=campaign.config.campaign_id,
                    completed_ids=tuple(completed),
                    failed_ids=tuple(failed),
                    output_refs=output_refs,
                    cursor=index,
                )
                (output / "campaign_checkpoint.json").write_text(
                    json.dumps(checkpoint_payload.as_dict(), indent=2, sort_keys=True),
                    encoding="utf-8",
                )
        checkpoint_result = CampaignCheckpoint(
            campaign_id=campaign.config.campaign_id,
            completed_ids=tuple(completed),
            failed_ids=tuple(failed),
            output_refs=output_refs,
            cursor=len(completed) + len(failed),
        )
        if output is not None:
            (output / "campaign_manifest.json").write_text(
                json.dumps(campaign.manifest.as_dict(), indent=2, sort_keys=True),
                encoding="utf-8",
            )
        return CampaignHistory(campaign_id=campaign.config.campaign_id, events=tuple(events)), checkpoint_result


def create_campaign(config: CampaignConfig) -> Campaign:
    """Create a deterministic campaign from a config."""

    experiments = generate_experiment_matrix(config)
    manifest = CampaignManifest(
        campaign_id=config.campaign_id,
        config_hash=stable_hash(config.as_dict()),
        experiment_count=len(experiments),
        experiment_ids=tuple(experiment.experiment_id for experiment in experiments),
        created_at=utc_timestamp(),
    )
    return Campaign(config=config, experiments=experiments, manifest=manifest)


def generate_experiment_matrix(config: CampaignConfig) -> tuple[ExperimentPlan, ...]:
    """Generate a reproducible experiment matrix."""

    parameter_names = tuple(sorted(config.parameter_grid))
    parameter_values = [tuple(config.parameter_grid[name]) for name in parameter_names]
    parameter_rows = (
        [dict(zip(parameter_names, values, strict=True)) for values in itertools.product(*parameter_values)]
        if parameter_names
        else [{}]
    )
    stages = _dimension(config.progression_stages)
    interventions = _dimension(config.interventions)
    scenarios = _dimension(config.custom_scenarios)
    plans: list[ExperimentPlan] = []
    for role, stage, intervention, scenario, parameters, seed, replicate in itertools.product(
        config.roles,
        stages,
        interventions,
        scenarios,
        parameter_rows,
        config.seeds,
        range(config.replicates),
    ):
        payload = {
            "campaign_id": config.campaign_id,
            "role": role,
            "progression_stage": stage,
            "intervention": intervention,
            "scenario": scenario,
            "parameters": parameters,
            "seed": int(seed),
            "replicate": int(replicate),
        }
        experiment_id = "exp_" + stable_hash(payload)[:16]
        plans.append(
            ExperimentPlan(
                experiment_id=experiment_id,
                campaign_id=config.campaign_id,
                role=str(role),
                seed=int(seed),
                replicate=int(replicate),
                parameters=dict(parameters),
                progression_stage=stage,
                intervention=intervention,
                scenario=scenario,
                metadata={"scientific_scope": CAMPAIGN_SCOPE},
            )
        )
    return tuple(plans)


def resume_campaign(campaign: Campaign, checkpoint: CampaignCheckpoint) -> CampaignResume:
    """Return the remaining plans after a checkpoint."""

    done = set(checkpoint.completed_ids) | set(checkpoint.failed_ids)
    remaining = tuple(plan for plan in campaign.experiments if plan.experiment_id not in done)
    return CampaignResume(remaining=remaining, checkpoint=checkpoint)


def load_campaign_config(path: str | Path) -> CampaignConfig:
    """Load a campaign config from JSON."""

    return CampaignConfig.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def save_campaign(campaign: Campaign, path: str | Path) -> Path:
    """Save a campaign plan to JSON."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(campaign.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return target


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _dimension(values: Sequence[str]) -> tuple[str | None, ...]:
    return tuple(values) if values else (None,)


def _event(plan: ExperimentPlan, status: str, started_at: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "experiment_id": plan.experiment_id,
        "campaign_id": plan.campaign_id,
        "status": status,
        "seed": plan.seed,
        "replicate": plan.replicate,
        "started_at": started_at,
        "finished_at": utc_timestamp(),
        "payload": _jsonable(payload),
    }


def _append_jsonl(path: Path, event: Mapping[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_jsonable(event), sort_keys=True) + "\n")


def _jsonable(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


__all__ = [
    "CAMPAIGN_SCOPE",
    "Campaign",
    "CampaignCheckpoint",
    "CampaignConfig",
    "CampaignHistory",
    "CampaignManifest",
    "CampaignResume",
    "CampaignRunner",
    "CampaignScheduler",
    "ExperimentPlan",
    "create_campaign",
    "generate_experiment_matrix",
    "load_campaign_config",
    "resume_campaign",
    "save_campaign",
    "utc_timestamp",
]
