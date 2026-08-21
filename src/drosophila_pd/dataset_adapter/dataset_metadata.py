"""Read dataset-level metadata without interpreting scientific results."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

import yaml


@dataclass(frozen=True)
class DatasetMetadata:
    """Metadata files found beside a dataset manifest."""

    files: tuple[Path, ...] = ()
    records: Mapping[str, Any] = field(default_factory=dict)
    errors: tuple[str, ...] = ()

    @property
    def available(self) -> bool:
        return bool(self.files) and not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "files": [path.as_posix() for path in self.files],
            "records": dict(self.records),
            "errors": list(self.errors),
            "available": self.available,
        }

    @classmethod
    def load(cls, root: str | Path, manifest: Mapping[str, Any] | None = None) -> "DatasetMetadata":
        dataset_root = Path(root).resolve()
        candidates: list[Path] = []
        declared = (manifest or {}).get("metadata")
        if isinstance(declared, str):
            candidates.append(dataset_root / declared)
        for name in ("metadata.json", "metadata.yaml", "metadata.yml"):
            candidates.append(dataset_root / name)
        metadata_dir = dataset_root / "metadata"
        if metadata_dir.is_dir():
            candidates.extend(sorted(path for path in metadata_dir.rglob("*") if path.suffix.casefold() in {".json", ".yaml", ".yml"}))
        files = tuple(dict.fromkeys(path.resolve() for path in candidates if path.is_file()))
        records: dict[str, Any] = {}
        errors: list[str] = []
        for path in files:
            try:
                records[path.relative_to(dataset_root).as_posix()] = _read(path)
            except (OSError, ValueError, yaml.YAMLError) as error:
                errors.append(f"{path.as_posix()}: {type(error).__name__}: {error}")
        return cls(files=files, records=records, errors=tuple(errors))


def _read(path: Path) -> Any:
    if path.suffix.casefold() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return yaml.safe_load(path.read_text(encoding="utf-8"))


__all__ = ["DatasetMetadata"]
