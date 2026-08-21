"""Deterministic artifact organization for v2 research campaigns."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.campaign_provenance import file_sha256


ARTIFACT_CATEGORIES = ("figures", "videos", "reports", "tables", "json", "csv", "logs", "datasets")


@dataclass(frozen=True)
class ManagedArtifact:
    """One artifact managed by the campaign artifact system."""

    category: str
    path: Path
    sha256: str
    byte_size: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "path": self.path.as_posix(),
            "sha256": self.sha256,
            "byte_size": int(self.byte_size),
        }


class CampaignArtifactManager:
    """Create and validate deterministic campaign artifact directories."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def prepare(self) -> dict[str, Path]:
        paths = {category: self.root / category for category in ARTIFACT_CATEGORIES}
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        return paths

    def register_file(self, source: str | Path, category: str, *, name: str | None = None) -> ManagedArtifact:
        if category not in ARTIFACT_CATEGORIES:
            raise ValueError(f"unsupported artifact category: {category}")
        paths = self.prepare()
        src = Path(source)
        if not src.is_file():
            raise FileNotFoundError(src)
        target = paths[category] / (name or src.name)
        if src.resolve() != target.resolve():
            shutil.copy2(src, target)
        return ManagedArtifact(category=category, path=target, sha256=file_sha256(target), byte_size=target.stat().st_size)

    def inventory(self) -> tuple[ManagedArtifact, ...]:
        artifacts: list[ManagedArtifact] = []
        for category in ARTIFACT_CATEGORIES:
            root = self.root / category
            if root.exists():
                for path in sorted(root.rglob("*")):
                    if path.is_file():
                        artifacts.append(
                            ManagedArtifact(
                                category=category,
                                path=path,
                                sha256=file_sha256(path),
                                byte_size=path.stat().st_size,
                            )
                        )
        return tuple(artifacts)

    def write_manifest(self, output_path: str | Path | None = None) -> Path:
        path = Path(output_path) if output_path is not None else self.root / "artifact_manifest.json"
        payload = {
            "artifact_manifest_version": 2,
            "categories": list(ARTIFACT_CATEGORIES),
            "artifacts": [artifact.as_dict() for artifact in self.inventory()],
            "scientific_scope": "Campaign artifacts are computational outputs only.",
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return path


def deterministic_artifact_layout(root: str | Path, campaign_id: str) -> dict[str, Path]:
    """Return deterministic output directories for a campaign."""

    manager = CampaignArtifactManager(Path(root) / campaign_id)
    return manager.prepare()


def artifact_manifest_from_paths(paths: Sequence[str | Path]) -> dict[str, Mapping[str, Any]]:
    """Create a compact hash manifest for arbitrary artifact paths."""

    manifest = {}
    for path in sorted(Path(item) for item in paths):
        if path.is_file():
            manifest[path.as_posix()] = {"sha256": file_sha256(path), "byte_size": path.stat().st_size}
    return manifest


__all__ = [
    "ARTIFACT_CATEGORIES",
    "CampaignArtifactManager",
    "ManagedArtifact",
    "artifact_manifest_from_paths",
    "deterministic_artifact_layout",
]
