"""Management layer for Digital Twin records built from imported rollouts.

The platform stores and compares existing computational state.  It does not
run FlyGym/MuJoCo, generate rollout data, calculate new scientific metrics, or
make biological claims.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
import uuid

from drosophila_pd.behavior_platform.digital_twin import (
    DIGITAL_TWIN_SCOPE,
    DigitalTwin,
    TwinHistory,
    TwinMetadata,
    TwinSnapshot,
    TwinState,
)


DIGITAL_TWIN_PLATFORM_SCOPE = (
    "Digital Twin workflow management over imported computational state only; "
    "no simulation, fabricated rollout, new scientific metric, or biological claim."
)
TWIN_ROLES = ("Healthy", "PD", "Candidate", "Control", "Validation", "Benchmark")
KNOWLEDGE_NODE_TYPES = (
    "Dataset",
    "Experiment",
    "Rollout",
    "DigitalFly",
    "Analysis",
    "Validation",
    "Report",
    "Publication",
)


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _write_json(path: Path, value: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(value), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


@dataclass(frozen=True)
class TwinAnnotation:
    """A user annotation linked to an existing twin state or artifact."""

    annotation_id: str
    twin_id: str
    kind: str
    content: str = ""
    start_time_s: float | None = None
    end_time_s: float | None = None
    frame: int | None = None
    target: str | None = None
    reference: str | None = None
    linked_figure: str | None = None
    author: str = ""
    created_at: str = field(default_factory=_timestamp)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "annotation_id": self.annotation_id,
            "twin_id": self.twin_id,
            "kind": self.kind,
            "content": self.content,
            "start_time_s": self.start_time_s,
            "end_time_s": self.end_time_s,
            "frame": self.frame,
            "target": self.target,
            "reference": self.reference,
            "linked_figure": self.linked_figure,
            "author": self.author,
            "created_at": self.created_at,
            "metadata": _jsonable(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TwinAnnotation":
        return cls(
            annotation_id=str(data["annotation_id"]),
            twin_id=str(data["twin_id"]),
            kind=str(data["kind"]),
            content=str(data.get("content", "")),
            start_time_s=data.get("start_time_s"),
            end_time_s=data.get("end_time_s"),
            frame=data.get("frame"),
            target=data.get("target"),
            reference=data.get("reference"),
            linked_figure=data.get("linked_figure"),
            author=str(data.get("author", "")),
            created_at=str(data.get("created_at", _timestamp())),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class DigitalTwinRecord:
    """Managed twin plus snapshots, bookmarks, and annotations."""

    twin: DigitalTwin
    role: str
    source_rollout: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    snapshots: dict[str, TwinSnapshot] = field(default_factory=dict)
    bookmarks: dict[str, str] = field(default_factory=dict)
    annotations: list[TwinAnnotation] = field(default_factory=list)
    restored_state: TwinState | None = None

    @property
    def twin_id(self) -> str:
        return self.twin.metadata.twin_id

    @property
    def state(self) -> TwinState | None:
        if self.restored_state is not None:
            return self.restored_state
        return self.twin.history.entries[-1] if self.twin.history.entries else None

    def as_dict(self) -> dict[str, Any]:
        return {
            "twin": self.twin.as_dict(),
            "role": self.role,
            "source_rollout": self.source_rollout,
            "metadata": _jsonable(self.metadata),
            "snapshots": {key: snapshot.as_dict() for key, snapshot in sorted(self.snapshots.items())},
            "bookmarks": dict(sorted(self.bookmarks.items())),
            "annotations": [annotation.as_dict() for annotation in self.annotations],
            "restored_state": self.restored_state.as_dict() if self.restored_state else None,
        }


class DigitalTwinManager:
    """Manage multiple role-labelled Digital Twin records."""

    def __init__(self) -> None:
        self.records: dict[str, DigitalTwinRecord] = {}

    def register(
        self,
        twin: DigitalTwin,
        *,
        role: str = "Validation",
        source_rollout: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> DigitalTwinRecord:
        if role not in TWIN_ROLES:
            raise ValueError(f"unsupported twin role: {role}")
        if twin.metadata.twin_id in self.records:
            raise ValueError(f"duplicate twin_id: {twin.metadata.twin_id}")
        record = DigitalTwinRecord(
            twin=twin,
            role=role,
            source_rollout=source_rollout,
            metadata=dict(metadata or {}),
        )
        self.records[record.twin_id] = record
        return record

    def register_imported_rollout(
        self,
        twin: DigitalTwin,
        source_rollout: str | Path,
        *,
        role: str = "Validation",
        metadata: Mapping[str, Any] | None = None,
    ) -> DigitalTwinRecord:
        """Register a caller-built twin and retain its imported rollout reference."""

        return self.register(
            twin,
            role=role,
            source_rollout=Path(source_rollout).as_posix(),
            metadata=metadata,
        )

    def get(self, twin_id: str) -> DigitalTwinRecord:
        try:
            return self.records[twin_id]
        except KeyError as error:
            raise KeyError(f"unknown twin_id: {twin_id}") from error

    def list(self, role: str | None = None) -> tuple[DigitalTwinRecord, ...]:
        values = tuple(self.records[key] for key in sorted(self.records))
        return tuple(record for record in values if role is None or record.role == role)

    def snapshot(self, twin_id: str, snapshot_id: str, *, time_s: float | None = None, bookmark: str | None = None) -> TwinSnapshot:
        record = self.get(twin_id)
        snapshot = record.twin.snapshot(snapshot_id, time_s=time_s)
        record.snapshots[snapshot_id] = snapshot
        if bookmark:
            record.bookmarks[str(bookmark)] = snapshot_id
        return snapshot

    def restore(self, twin_id: str, snapshot_id: str) -> TwinState:
        record = self.get(twin_id)
        snapshot = record.snapshots[snapshot_id]
        record.restored_state = snapshot.state
        return snapshot.state

    def branch(self, twin_id: str, snapshot_id: str, new_twin_id: str, *, role: str | None = None) -> DigitalTwinRecord:
        source = self.get(twin_id)
        snapshot = source.snapshots[snapshot_id]
        if new_twin_id in self.records:
            raise ValueError(f"duplicate twin_id: {new_twin_id}")
        metadata = TwinMetadata(
            twin_id=new_twin_id,
            source=source.twin.metadata.source,
            git_commit=source.twin.metadata.git_commit,
            tags=source.twin.metadata.tags,
            provenance={**dict(source.twin.metadata.provenance), "branched_from": twin_id, "snapshot_id": snapshot_id},
        )
        twin = DigitalTwin(
            metadata=metadata,
            configuration=source.twin.configuration,
            history=TwinHistory(entries=(snapshot.state,)),
            scenarios=source.twin.scenarios,
        )
        return self.register(twin, role=role or source.role, source_rollout=source.source_rollout, metadata={"branched_from": twin_id})

    def add_bookmark(self, twin_id: str, name: str, snapshot_id: str) -> str:
        record = self.get(twin_id)
        if snapshot_id not in record.snapshots:
            raise KeyError(f"unknown snapshot_id: {snapshot_id}")
        record.bookmarks[str(name)] = snapshot_id
        return snapshot_id

    def compare_snapshots(self, twin_id: str, left_id: str, right_id: str) -> "StateDiff":
        record = self.get(twin_id)
        return StateDiffEngine.compare(record.snapshots[left_id].state, record.snapshots[right_id].state)

    def annotate(self, annotation: TwinAnnotation) -> TwinAnnotation:
        record = self.get(annotation.twin_id)
        record.annotations.append(annotation)
        return annotation

    def as_dict(self) -> dict[str, Any]:
        return {
            "digital_twin_manager_version": 1,
            "roles": list(TWIN_ROLES),
            "records": [record.as_dict() for record in self.list()],
            "scientific_scope": DIGITAL_TWIN_PLATFORM_SCOPE,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DigitalTwinManager":
        manager = cls()
        for item in data.get("records", ()):
            twin = DigitalTwin.from_dict(item["twin"])
            snapshots = {
                key: _snapshot_from_dict(value)
                for key, value in item.get("snapshots", {}).items()
            }
            record = DigitalTwinRecord(
                twin=twin,
                role=str(item.get("role", "Validation")),
                source_rollout=item.get("source_rollout"),
                metadata=dict(item.get("metadata", {})),
                snapshots=snapshots,
                bookmarks=dict(item.get("bookmarks", {})),
                annotations=[TwinAnnotation.from_dict(value) for value in item.get("annotations", ())],
                restored_state=_state_from_dict(item["restored_state"]) if item.get("restored_state") else None,
            )
            manager.records[record.twin_id] = record
        return manager

    def to_json(self, path: str | Path) -> Path:
        return _write_json(Path(path), self.as_dict())

    @classmethod
    def from_json(cls, path: str | Path) -> "DigitalTwinManager":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


@dataclass(frozen=True)
class StateDiff:
    """Structured difference of existing state fields."""

    joint_changes: Mapping[str, Any] = field(default_factory=dict)
    com_changes: Mapping[str, Any] = field(default_factory=dict)
    trajectory_changes: Mapping[str, Any] = field(default_factory=dict)
    metrics_delta: Mapping[str, Any] = field(default_factory=dict)
    behavior_delta: Mapping[str, Any] = field(default_factory=dict)
    parameter_changes: Mapping[str, Any] = field(default_factory=dict)
    changed_fields: tuple[str, ...] = ()
    scientific_scope: str = DIGITAL_TWIN_PLATFORM_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "joint_changes": _jsonable(self.joint_changes),
            "com_changes": _jsonable(self.com_changes),
            "trajectory_changes": _jsonable(self.trajectory_changes),
            "metrics_delta": _jsonable(self.metrics_delta),
            "behavior_delta": _jsonable(self.behavior_delta),
            "parameter_changes": _jsonable(self.parameter_changes),
            "changed_fields": list(self.changed_fields),
            "scientific_scope": self.scientific_scope,
        }


class StateDiffEngine:
    """Compare state mappings without deriving new metrics."""

    @staticmethod
    def compare(left: TwinState, right: TwinState) -> StateDiff:
        metrics = _mapping_delta(left.metrics, right.metrics)
        grouped = {"joint": {}, "com": {}, "trajectory": {}}
        for key, value in metrics.items():
            lowered = key.casefold()
            for group in grouped:
                if group in lowered:
                    grouped[group][key] = value
        behavior = {} if left.state_label == right.state_label else {"left": left.state_label, "right": right.state_label}
        parameters = _mapping_delta(left.parameters, right.parameters)
        changed = tuple(sorted(set(metrics) | set(parameters) | ({"state_label"} if behavior else set())))
        return StateDiff(
            joint_changes=grouped["joint"],
            com_changes=grouped["com"],
            trajectory_changes=grouped["trajectory"],
            metrics_delta=metrics,
            behavior_delta=behavior,
            parameter_changes=parameters,
            changed_fields=changed,
        )


class TemporalExplorer:
    """Select existing history entries by time, behavior, bookmarks, or events."""

    def select(
        self,
        record: DigitalTwinRecord,
        *,
        start_time_s: float | None = None,
        end_time_s: float | None = None,
        behavior: str | None = None,
        bookmark: str | None = None,
        event: str | None = None,
    ) -> tuple[TwinState, ...]:
        start = start_time_s
        end = end_time_s
        if bookmark is not None:
            snapshot_id = record.bookmarks[bookmark]
            point = record.snapshots[snapshot_id].state.time_s
            start = point if start is None else start
            end = point if end is None else end
        states = record.twin.history.entries
        return tuple(
            state
            for state in states
            if (start is None or state.time_s >= start)
            and (end is None or state.time_s <= end)
            and (behavior is None or state.state_label == behavior)
            and (event is None or state.metadata.get("event") == event)
        )

    def segments(self, record: DigitalTwinRecord, *, behavior: str | None = None) -> tuple[tuple[TwinState, ...], ...]:
        states = self.select(record, behavior=behavior)
        if not states:
            return ()
        groups: list[list[TwinState]] = [[states[0]]]
        for state in states[1:]:
            if state.state_label == groups[-1][-1].state_label:
                groups[-1].append(state)
            else:
                groups.append([state])
        return tuple(tuple(group) for group in groups)


@dataclass
class ScenarioRecord:
    scenario_id: str
    twin_ids: tuple[str, ...] = ()
    experiments: list[Mapping[str, Any]] = field(default_factory=list)
    observations: list[Mapping[str, Any]] = field(default_factory=list)
    analyses: list[Mapping[str, Any]] = field(default_factory=list)
    conclusions: list[Mapping[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add(self, collection: str, value: Mapping[str, Any]) -> Mapping[str, Any]:
        target = getattr(self, collection, None)
        if not isinstance(target, list):
            raise ValueError(f"unsupported scenario collection: {collection}")
        target.append(dict(value))
        return value

    def as_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "twin_ids": list(self.twin_ids),
            "experiments": _jsonable(self.experiments),
            "observations": _jsonable(self.observations),
            "analyses": _jsonable(self.analyses),
            "conclusions": _jsonable(self.conclusions),
            "metadata": _jsonable(self.metadata),
        }


class ScenarioWorkspace:
    """Organize scenario workflow records without executing analysis."""

    def __init__(self) -> None:
        self.scenarios: dict[str, ScenarioRecord] = {}

    def create(self, scenario_id: str, *, twin_ids: Sequence[str] = (), metadata: Mapping[str, Any] | None = None) -> ScenarioRecord:
        if scenario_id in self.scenarios:
            raise ValueError(f"duplicate scenario_id: {scenario_id}")
        record = ScenarioRecord(scenario_id, tuple(twin_ids), metadata=dict(metadata or {}))
        self.scenarios[scenario_id] = record
        return record

    def get(self, scenario_id: str) -> ScenarioRecord:
        return self.scenarios[scenario_id]

    def add(self, scenario_id: str, collection: str, value: Mapping[str, Any]) -> Mapping[str, Any]:
        return self.get(scenario_id).add(collection, value)

    def as_dict(self) -> dict[str, Any]:
        return {"scenarios": [self.scenarios[key].as_dict() for key in sorted(self.scenarios)], "scientific_scope": DIGITAL_TWIN_PLATFORM_SCOPE}


@dataclass
class KnowledgeGraph:
    """Explicit links among dataset, experiment, rollout, twin, and reports."""

    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)

    def add_node(self, node_type: str, node_id: str, **metadata: Any) -> str:
        if node_type not in KNOWLEDGE_NODE_TYPES:
            raise ValueError(f"unsupported knowledge node type: {node_type}")
        key = f"{node_type}:{node_id}"
        self.nodes[key] = {"type": node_type, "id": node_id, "metadata": _jsonable(metadata)}
        return key

    def link(self, source_type: str, source_id: str, target_type: str, target_id: str, relation: str) -> dict[str, Any]:
        source = self.add_node(source_type, source_id)
        target = self.add_node(target_type, target_id)
        edge = {"source": source, "target": target, "relation": str(relation)}
        if edge not in self.edges:
            self.edges.append(edge)
        return edge

    def from_twin_manager(self, manager: DigitalTwinManager) -> "KnowledgeGraph":
        for record in manager.list():
            self.add_node("DigitalFly", record.twin_id, role=record.role, source_rollout=record.source_rollout)
            if record.source_rollout:
                self.link("Rollout", record.source_rollout, "DigitalFly", record.twin_id, "materializes")
        return self

    def as_dict(self) -> dict[str, Any]:
        return {"nodes": list(self.nodes.values()), "edges": list(self.edges), "scientific_scope": DIGITAL_TWIN_PLATFORM_SCOPE}


@dataclass
class VirtualLaboratorySession:
    """Serializable view state for one research session."""

    session_id: str
    camera: Mapping[str, Any] = field(default_factory=dict)
    layout: Mapping[str, Any] = field(default_factory=dict)
    selection: Mapping[str, Any] = field(default_factory=dict)
    opened_panels: tuple[str, ...] = ()
    timeline: Mapping[str, Any] = field(default_factory=dict)
    notes: tuple[str, ...] = ()
    filters: Mapping[str, Any] = field(default_factory=dict)
    overlays: Mapping[str, Any] = field(default_factory=dict)
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "camera": _jsonable(self.camera),
            "layout": _jsonable(self.layout),
            "selection": _jsonable(self.selection),
            "opened_panels": list(self.opened_panels),
            "timeline": _jsonable(self.timeline),
            "notes": list(self.notes),
            "filters": _jsonable(self.filters),
            "overlays": _jsonable(self.overlays),
            "metadata": _jsonable(self.metadata),
        }

    def save(self, path: str | Path) -> Path:
        return _write_json(Path(path), self.as_dict())

    @classmethod
    def load(cls, path: str | Path) -> "VirtualLaboratorySession":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            session_id=str(data["session_id"]),
            camera=dict(data.get("camera", {})),
            layout=dict(data.get("layout", {})),
            selection=dict(data.get("selection", {})),
            opened_panels=tuple(data.get("opened_panels", ())),
            timeline=dict(data.get("timeline", {})),
            notes=tuple(data.get("notes", ())),
            filters=dict(data.get("filters", {})),
            overlays=dict(data.get("overlays", {})),
            metadata=dict(data.get("metadata", {})),
        )


@dataclass
class CollaborationLayer:
    """Review metadata and changelog for collaborative sessions."""

    comments: list[Mapping[str, Any]] = field(default_factory=list)
    approvals: list[Mapping[str, Any]] = field(default_factory=list)
    history: list[Mapping[str, Any]] = field(default_factory=list)
    change_log: list[Mapping[str, Any]] = field(default_factory=list)

    def comment(self, author: str, content: str, *, target: str | None = None) -> Mapping[str, Any]:
        item = {"comment_id": str(uuid.uuid4()), "author": author, "content": content, "target": target, "timestamp": _timestamp()}
        self.comments.append(item)
        self.history.append({"kind": "comment", **item})
        return item

    def approve(self, author: str, *, target: str, approved: bool = True) -> Mapping[str, Any]:
        item = {"target": target, "author": author, "approved": bool(approved), "timestamp": _timestamp()}
        self.approvals.append(item)
        self.history.append({"kind": "approval", **item})
        return item

    def record_change(self, author: str, change: str, *, target: str | None = None) -> Mapping[str, Any]:
        item = {"author": author, "change": change, "target": target, "timestamp": _timestamp()}
        self.change_log.append(item)
        self.history.append({"kind": "change", **item})
        return item

    def as_dict(self) -> dict[str, Any]:
        return {"comments": _jsonable(self.comments), "approvals": _jsonable(self.approvals), "history": _jsonable(self.history), "change_log": _jsonable(self.change_log), "scientific_scope": DIGITAL_TWIN_PLATFORM_SCOPE}


class DigitalTwinPlatform:
    """Aggregate Milestone 4 managers while preserving explicit boundaries."""

    def __init__(self) -> None:
        self.twins = DigitalTwinManager()
        self.scenarios = ScenarioWorkspace()
        self.graph = KnowledgeGraph()
        self.sessions: dict[str, VirtualLaboratorySession] = {}
        self.collaboration = CollaborationLayer()
        self.temporal = TemporalExplorer()

    def add_session(self, session: VirtualLaboratorySession) -> VirtualLaboratorySession:
        self.sessions[session.session_id] = session
        return session

    def snapshot(self) -> dict[str, Any]:
        return {
            "platform_version": 1,
            "twins": self.twins.as_dict(),
            "scenarios": self.scenarios.as_dict(),
            "knowledge_graph": self.graph.as_dict(),
            "sessions": [self.sessions[key].as_dict() for key in sorted(self.sessions)],
            "collaboration": self.collaboration.as_dict(),
            "scientific_scope": DIGITAL_TWIN_PLATFORM_SCOPE,
        }

    def to_json(self, path: str | Path) -> Path:
        return _write_json(Path(path), self.snapshot())

    @classmethod
    def from_json(cls, path: str | Path) -> "DigitalTwinPlatform":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        platform = cls()
        platform.twins = DigitalTwinManager.from_dict(data.get("twins", {}))
        platform.scenarios = _scenario_workspace_from_dict(data.get("scenarios", {}))
        graph_data = data.get("knowledge_graph", {})
        raw_nodes = graph_data.get("nodes", ())
        if isinstance(raw_nodes, Mapping):
            nodes = {key: dict(value) for key, value in raw_nodes.items()}
        else:
            nodes = {
                f"{item['type']}:{item['id']}": dict(item)
                for item in raw_nodes
            }
        platform.graph = KnowledgeGraph(nodes=nodes, edges=list(graph_data.get("edges", ())))
        platform.sessions = {
            item["session_id"]: _session_from_dict(item)
            for item in data.get("sessions", ())
        }
        collaboration = data.get("collaboration", {})
        platform.collaboration = CollaborationLayer(
            comments=list(collaboration.get("comments", ())),
            approvals=list(collaboration.get("approvals", ())),
            history=list(collaboration.get("history", ())),
            change_log=list(collaboration.get("change_log", ())),
        )
        return platform


def _snapshot_from_dict(data: Mapping[str, Any]) -> TwinSnapshot:
    return TwinSnapshot(
        snapshot_id=str(data["snapshot_id"]),
        state=_state_from_dict(data["state"]),
        metadata=dict(data.get("metadata", {})),
    )


def _state_from_dict(data: Mapping[str, Any]) -> TwinState:
    return TwinState(
        time_s=float(data["time_s"]),
        state_label=str(data["state_label"]),
        metrics=dict(data.get("metrics", {})),
        parameters=dict(data.get("parameters", {})),
        metadata=dict(data.get("metadata", {})),
    )


def _scenario_workspace_from_dict(data: Mapping[str, Any]) -> ScenarioWorkspace:
    workspace = ScenarioWorkspace()
    for item in data.get("scenarios", ()):
        scenario = workspace.create(item["scenario_id"], twin_ids=item.get("twin_ids", ()), metadata=item.get("metadata", {}))
        for collection in ("experiments", "observations", "analyses", "conclusions"):
            getattr(scenario, collection).extend(item.get(collection, ()))
    return workspace


def _session_from_dict(data: Mapping[str, Any]) -> VirtualLaboratorySession:
    return VirtualLaboratorySession(
        session_id=str(data["session_id"]),
        camera=dict(data.get("camera", {})),
        layout=dict(data.get("layout", {})),
        selection=dict(data.get("selection", {})),
        opened_panels=tuple(data.get("opened_panels", ())),
        timeline=dict(data.get("timeline", {})),
        notes=tuple(data.get("notes", ())),
        filters=dict(data.get("filters", {})),
        overlays=dict(data.get("overlays", {})),
        metadata=dict(data.get("metadata", {})),
    )


def _mapping_delta(left: Mapping[str, Any], right: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key in sorted(set(left) | set(right)):
        left_value = left.get(key)
        right_value = right.get(key)
        if _values_equal(left_value, right_value):
            continue
        if isinstance(left_value, (int, float)) and isinstance(right_value, (int, float)):
            result[str(key)] = {"left": left_value, "right": right_value, "delta": right_value - left_value}
        else:
            result[str(key)] = {"left": _jsonable(left_value), "right": _jsonable(right_value)}
    return result


def _values_equal(left: Any, right: Any) -> bool:
    try:
        return json.dumps(_jsonable(left), sort_keys=True) == json.dumps(_jsonable(right), sort_keys=True)
    except (TypeError, ValueError):
        return left == right


__all__ = [
    "DIGITAL_TWIN_PLATFORM_SCOPE",
    "DIGITAL_TWIN_SCOPE",
    "KNOWLEDGE_NODE_TYPES",
    "TWIN_ROLES",
    "CollaborationLayer",
    "DigitalTwinManager",
    "DigitalTwinPlatform",
    "DigitalTwinRecord",
    "KnowledgeGraph",
    "ScenarioRecord",
    "ScenarioWorkspace",
    "StateDiff",
    "StateDiffEngine",
    "TemporalExplorer",
    "TwinAnnotation",
    "VirtualLaboratorySession",
]
