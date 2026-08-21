"""Experiment summary generation."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass
class ExperimentSummary:
    """Compact runtime summary, separate from scientific analysis output."""

    experiment_id: str
    state: str
    dataset: Mapping[str, Any] = field(default_factory=dict)
    campaign: Mapping[str, Any] = field(default_factory=dict)
    duration_seconds: float = 0.0
    stages: list[Mapping[str, Any]] = field(default_factory=list)
    validation: Mapping[str, Any] = field(default_factory=dict)
    artifacts: list[Mapping[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "summary_version": 1,
            "experiment_id": self.experiment_id,
            "state": self.state,
            "dataset": _jsonable(self.dataset),
            "campaign": _jsonable(self.campaign),
            "duration_seconds": float(self.duration_seconds),
            "stages": _jsonable(self.stages),
            "validation": _jsonable(self.validation),
            "artifacts": _jsonable(self.artifacts),
            "warnings": list(self.warnings),
            "scientific_scope": "Runtime summary only; no new scientific result or biological claim.",
        }

    def write(self, json_path: str | Path, markdown_path: str | Path) -> tuple[Path, Path]:
        json_target, markdown_target = Path(json_path), Path(markdown_path)
        json_target.parent.mkdir(parents=True, exist_ok=True)
        json_target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_target.write_text(_markdown(self.as_dict()), encoding="utf-8")
        return json_target, markdown_target


def _markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Experiment Summary",
        "",
        f"- Experiment: `{payload['experiment_id']}`",
        f"- State: `{payload['state']}`",
        f"- Duration (s): `{payload['duration_seconds']:.6f}`",
        "- Scope: runtime orchestration only.",
        "",
        "## Stages",
        "",
        "| Stage | Status |",
        "| --- | --- |",
    ]
    lines.extend(f"| {item.get('stage', item.get('name', 'unknown'))} | {item.get('status', 'unknown')} |" for item in payload["stages"])
    lines.extend(["", "## Dataset", "", f"- State: `{payload['dataset'].get('state', 'unknown')}`", f"- Found: `{len(payload['dataset'].get('datasets', ()))}`", "", "## Artifacts", ""])
    if payload["artifacts"]:
        lines.extend(f"- `{item.get('category', 'artifact')}`: `{item.get('path', '')}`" for item in payload["artifacts"])
    else:
        lines.append("- None.")
    if payload["warnings"]:
        lines.extend(["", "## Warnings", "", *[f"- {item}" for item in payload["warnings"]]])
    return "\n".join(lines) + "\n"


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


__all__ = ["ExperimentSummary"]
