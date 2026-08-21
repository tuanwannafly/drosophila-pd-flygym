"""Persistence and artifact registration for experiment sessions."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import zipfile

from drosophila_pd.research_execution import ArtifactRegistry


@dataclass(frozen=True)
class OutputPaths:
    root: Path
    session: Path
    execution: Path
    runtime_state: Path
    artifacts: Path
    manifest: Path
    summary_json: Path
    summary_markdown: Path

    @classmethod
    def from_root(cls, root: str | Path) -> "OutputPaths":
        base = Path(root).resolve()
        return cls(
            root=base,
            session=base / "session.json",
            execution=base / "execution.json",
            runtime_state=base / "runtime_state.json",
            artifacts=base / "artifacts.json",
            manifest=base / "manifest.json",
            summary_json=base / "experiment_summary.json",
            summary_markdown=base / "experiment_summary.md",
        )


class ExperimentOutputs:
    """Write only runtime metadata and register existing downstream files."""

    def __init__(self, root: str | Path) -> None:
        self.paths = OutputPaths.from_root(root)
        self.paths.root.mkdir(parents=True, exist_ok=True)

    def write_json(self, path: Path, payload: Mapping[str, Any]) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def write_empty_artifacts(self) -> Path:
        return ArtifactRegistry(self.paths.root).write(self.paths.artifacts)

    def register_study(self, study_result: Any) -> list[dict[str, Any]]:
        registry = ArtifactRegistry(self.paths.root)
        study_root = Path(getattr(study_result, "study_root", self.paths.root / "study_outputs"))
        registry.register_tree(study_root)
        package_path = getattr(study_result, "package_path", None)
        if package_path and Path(package_path).is_file():
            registry.register(package_path, "bundle")
        registry.write(self.paths.artifacts)
        return [record.as_dict() for record in registry.records]

    def archive(self) -> Path:
        target = self.paths.root / "experiment_archive.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(self.paths.root.rglob("*")):
                if path.is_file() and path != target:
                    archive.write(path, path.relative_to(self.paths.root).as_posix())
        return target


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


__all__ = ["ExperimentOutputs", "OutputPaths"]
