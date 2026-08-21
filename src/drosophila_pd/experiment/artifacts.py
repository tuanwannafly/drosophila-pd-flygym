"""Deterministic per-experiment artifact layout and publication registration."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from drosophila_pd.behavior_platform.campaign_provenance import file_sha256

from .models import ARTIFACT_DIRECTORIES, SCIENTIFIC_SCOPE


@dataclass
class ArtifactLayout:
    """Manage directories for one experiment without inventing output data."""

    root: Path | str

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    def prepare(self) -> dict[str, Path]:
        paths = {name: self.root / name for name in ARTIFACT_DIRECTORIES}
        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)
        return paths

    @property
    def manifest_path(self) -> Path:
        return self.root / "manifest.json"

    def register_file(
        self,
        source: str | Path,
        category: str,
        *,
        name: str | None = None,
    ) -> Path:
        if category not in ARTIFACT_DIRECTORIES:
            raise ValueError(f"unsupported artifact category: {category}")
        source_path = Path(source)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        target_dir = self.prepare()[category]
        target = target_dir / (name or source_path.name)
        target.parent.mkdir(parents=True, exist_ok=True)
        if source_path.resolve() != target.resolve():
            shutil.copy2(source_path, target)
        return target

    def inventory(self) -> dict[str, dict[str, Any]]:
        self.prepare()
        records: dict[str, dict[str, Any]] = {}
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path == self.manifest_path:
                continue
            relative = path.relative_to(self.root).as_posix()
            records[relative] = {
                "sha256": file_sha256(path),
                "byte_size": path.stat().st_size,
            }
        return records

    def write_manifest(self, *, metadata: Mapping[str, Any] | None = None) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        payload = {
            "artifact_manifest_version": 1,
            "root": self.root.as_posix(),
            "artifacts": self.inventory(),
            "metadata": dict(metadata or {}),
            "scientific_scope": SCIENTIFIC_SCOPE,
        }
        self.manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        return self.manifest_path


class PublicationAssetManager:
    """Register existing figures/tables for publication without generating data."""

    def __init__(self, layout: ArtifactLayout) -> None:
        self.layout = layout
        self._figures: list[dict[str, Any]] = []
        self._tables: list[dict[str, Any]] = []

    def register_figure(
        self,
        source: str | Path,
        *,
        identifier: str | None = None,
        caption: str = "",
        manuscript_section: str | None = None,
    ) -> Path:
        target = self.layout.register_file(source, "publication", name=f"figures/{Path(source).name}")
        number = len(self._figures) + 1
        self._figures.append(
            {
                "identifier": identifier or f"Figure {number}",
                "filename": target.relative_to(self.layout.root).as_posix(),
                "caption": caption,
                "manuscript_section": manuscript_section,
                "sha256": file_sha256(target),
            }
        )
        return target

    def register_table(
        self,
        source: str | Path,
        *,
        identifier: str | None = None,
        caption: str = "",
        manuscript_section: str | None = None,
    ) -> Path:
        target = self.layout.register_file(source, "publication", name=f"tables/{Path(source).name}")
        number = len(self._tables) + 1
        self._tables.append(
            {
                "identifier": identifier or f"Table {number}",
                "filename": target.relative_to(self.layout.root).as_posix(),
                "caption": caption,
                "manuscript_section": manuscript_section,
                "sha256": file_sha256(target),
            }
        )
        return target

    def write_manifests(self) -> dict[str, Path]:
        publication = self.layout.prepare()["publication"]
        figure_path = publication / "figure_manifest.json"
        table_path = publication / "table_manifest.json"
        caption_path = publication / "caption_templates.json"
        figure_path.write_text(json.dumps({"figures": self._figures}, indent=2, sort_keys=True), encoding="utf-8")
        table_path.write_text(json.dumps({"tables": self._tables}, indent=2, sort_keys=True), encoding="utf-8")
        caption_path.write_text(
            json.dumps(
                {
                    "figure": "Figure {number}. {caption}",
                    "table": "Table {number}. {caption}",
                    "scientific_scope": SCIENTIFIC_SCOPE,
                },
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )
        self.layout.write_manifest(metadata={"publication_manifests": True})
        return {"figures": figure_path, "tables": table_path, "captions": caption_path}


# The public name mirrors the product terminology while retaining the more
# precise layout implementation internally.
ArtifactManager = ArtifactLayout


__all__ = ["ArtifactLayout", "ArtifactManager", "PublicationAssetManager"]
