"""Digital twin core for v2 behavioral replay and scenario records."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


DIGITAL_TWIN_SCOPE = (
    "Computational digital twin record only. This object stores simulated "
    "state, metadata, scenarios, and replay history; it does not run FlyGym, "
    "alter perturbations, or make biological validation claims."
)


@dataclass(frozen=True)
class TwinMetadata:
    """Provenance metadata for one computational twin."""

    twin_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    source: str = "repository_v2_behavior_platform"
    git_commit: str | None = None
    tags: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "created_at": self.created_at,
            "source": self.source,
            "git_commit": self.git_commit,
            "tags": list(self.tags),
            "provenance": dict(self.provenance),
        }


@dataclass(frozen=True)
class TwinConfiguration:
    """Versioned computational configuration for a twin."""

    config_id: str
    version: str
    parameters: Mapping[str, Any]
    schema_version: str = "v2.digital_twin.1"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "config_id": self.config_id,
            "version": self.version,
            "schema_version": self.schema_version,
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TwinState:
    """One timestamped computational twin state."""

    time_s: float
    state_label: str
    metrics: Mapping[str, Any] = field(default_factory=dict)
    parameters: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "time_s": float(self.time_s),
            "state_label": self.state_label,
            "metrics": dict(self.metrics),
            "parameters": dict(self.parameters),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TwinSnapshot:
    """Named immutable snapshot of a twin state."""

    snapshot_id: str
    state: TwinState
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "state": self.state.as_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TwinHistory:
    """Ordered state timeline for deterministic reconstruction."""

    entries: tuple[TwinState, ...] = ()

    def append(self, state: TwinState) -> "TwinHistory":
        entries = tuple(sorted((*self.entries, state), key=lambda item: item.time_s))
        return TwinHistory(entries=entries)

    def as_dict(self) -> dict[str, Any]:
        return {
            "entry_count": len(self.entries),
            "entries": [entry.as_dict() for entry in self.entries],
        }

    def state_at(self, time_s: float) -> TwinState:
        if not self.entries:
            raise ValueError("twin history has no states.")
        selected = self.entries[0]
        for state in self.entries:
            if state.time_s <= time_s:
                selected = state
        return selected


@dataclass(frozen=True)
class TwinReplay:
    """Deterministic replay of a twin history at requested sample times."""

    twin_id: str
    sample_times_s: tuple[float, ...]
    states: tuple[TwinState, ...]
    deterministic: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "twin_id": self.twin_id,
            "sample_times_s": [float(value) for value in self.sample_times_s],
            "states": [state.as_dict() for state in self.states],
            "deterministic": bool(self.deterministic),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class TwinScenario:
    """Scenario attached to a digital twin."""

    scenario_id: str
    role: str
    configuration: TwinConfiguration
    initial_state: TwinState
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "role": self.role,
            "configuration": self.configuration.as_dict(),
            "initial_state": self.initial_state.as_dict(),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class DigitalTwin:
    """Serializable computational twin with history and scenarios."""

    metadata: TwinMetadata
    configuration: TwinConfiguration
    history: TwinHistory = TwinHistory()
    scenarios: tuple[TwinScenario, ...] = ()

    def record_state(self, state: TwinState) -> "DigitalTwin":
        """Return a twin with ``state`` added to the ordered history."""

        return DigitalTwin(
            metadata=self.metadata,
            configuration=self.configuration,
            history=self.history.append(state),
            scenarios=self.scenarios,
        )

    def add_scenario(self, scenario: TwinScenario) -> "DigitalTwin":
        """Return a twin with one additional scenario."""

        return DigitalTwin(
            metadata=self.metadata,
            configuration=self.configuration,
            history=self.history,
            scenarios=(*self.scenarios, scenario),
        )

    def snapshot(self, snapshot_id: str, *, time_s: float | None = None) -> TwinSnapshot:
        """Create a snapshot at the latest state or requested time."""

        if not self.history.entries:
            raise ValueError("cannot snapshot a twin with empty history.")
        state = self.history.entries[-1] if time_s is None else self.history.state_at(float(time_s))
        return TwinSnapshot(snapshot_id=snapshot_id, state=state, metadata={"twin_id": self.metadata.twin_id})

    def replay(self, sample_times_s: Sequence[float]) -> TwinReplay:
        """Replay nearest historical state at each requested time."""

        if not self.history.entries:
            raise ValueError("cannot replay a twin with empty history.")
        times = tuple(float(value) for value in sample_times_s)
        return TwinReplay(
            twin_id=self.metadata.twin_id,
            sample_times_s=times,
            states=tuple(self.history.state_at(value) for value in times),
            metadata={"configuration_version": self.configuration.version},
        )

    def reconstruct_timeline(self) -> list[dict[str, Any]]:
        """Return JSON-ready ordered timeline states."""

        return [entry.as_dict() for entry in self.history.entries]

    def as_dict(self) -> dict[str, Any]:
        return {
            "digital_twin_version": 2,
            "scientific_scope": DIGITAL_TWIN_SCOPE,
            "metadata": self.metadata.as_dict(),
            "configuration": self.configuration.as_dict(),
            "history": self.history.as_dict(),
            "scenarios": [scenario.as_dict() for scenario in self.scenarios],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DigitalTwin":
        """Deserialize a digital twin from a JSON-like mapping."""

        metadata_data = data["metadata"]
        config_data = data["configuration"]
        metadata = TwinMetadata(
            twin_id=str(metadata_data["twin_id"]),
            created_at=str(metadata_data.get("created_at", "")),
            source=str(metadata_data.get("source", "repository_v2_behavior_platform")),
            git_commit=metadata_data.get("git_commit"),
            tags=tuple(metadata_data.get("tags", ())),
            provenance=dict(metadata_data.get("provenance", {})),
        )
        configuration = TwinConfiguration(
            config_id=str(config_data["config_id"]),
            version=str(config_data["version"]),
            schema_version=str(config_data.get("schema_version", "v2.digital_twin.1")),
            parameters=dict(config_data.get("parameters", {})),
            metadata=dict(config_data.get("metadata", {})),
        )
        history = TwinHistory(
            entries=tuple(_state_from_dict(item) for item in data.get("history", {}).get("entries", ()))
        )
        scenarios = tuple(_scenario_from_dict(item) for item in data.get("scenarios", ()))
        return cls(metadata=metadata, configuration=configuration, history=history, scenarios=scenarios)

    def to_json(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return path

    @classmethod
    def from_json(cls, path: str | Path) -> "DigitalTwin":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _state_from_dict(data: Mapping[str, Any]) -> TwinState:
    return TwinState(
        time_s=float(data["time_s"]),
        state_label=str(data["state_label"]),
        metrics=dict(data.get("metrics", {})),
        parameters=dict(data.get("parameters", {})),
        metadata=dict(data.get("metadata", {})),
    )


def _scenario_from_dict(data: Mapping[str, Any]) -> TwinScenario:
    return TwinScenario(
        scenario_id=str(data["scenario_id"]),
        role=str(data["role"]),
        configuration=TwinConfiguration(
            config_id=str(data["configuration"]["config_id"]),
            version=str(data["configuration"]["version"]),
            schema_version=str(data["configuration"].get("schema_version", "v2.digital_twin.1")),
            parameters=dict(data["configuration"].get("parameters", {})),
            metadata=dict(data["configuration"].get("metadata", {})),
        ),
        initial_state=_state_from_dict(data["initial_state"]),
        metadata=dict(data.get("metadata", {})),
    )


__all__ = [
    "DIGITAL_TWIN_SCOPE",
    "DigitalTwin",
    "TwinConfiguration",
    "TwinHistory",
    "TwinMetadata",
    "TwinReplay",
    "TwinScenario",
    "TwinSnapshot",
    "TwinState",
]
