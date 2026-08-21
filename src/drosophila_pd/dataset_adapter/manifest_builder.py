"""Build an in-memory manifest view from existing dataset files."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping

from .flygym_dataset import FlyGymDataset


class ManifestBuilder:
    """Create a manifest representation without copying or altering payloads."""

    def build(
        self,
        dataset: FlyGymDataset,
        *,
        source_commit: str = "",
        citation: str = "",
        scientific_scope: str = "Computational FlyGym rollout data only; not biological validation.",
    ) -> dict[str, Any]:
        entries = []
        checksums = {}
        for item in dataset.rollout_files:
            if not item.exists:
                continue
            entries.append({
                "relative_path": item.relative_path,
                "byte_size": item.observed_byte_size,
                "sha256": item.observed_sha256,
                **({"experiment_id": item.experiment_id} if item.experiment_id else {}),
            })
            if item.observed_sha256:
                checksums[item.relative_path] = item.observed_sha256
        return {
            "schema_version": "1.0",
            "dataset_id": dataset.dataset_id,
            "dataset_type": dataset.dataset_type,
            "dataset_version": dataset.dataset_version,
            "source_commit": source_commit,
            "created_at": datetime.now(UTC).isoformat(),
            "entries": entries,
            "checksums": checksums,
            "citation": citation,
            "scientific_scope": scientific_scope,
        }

    def write(self, manifest: Mapping[str, Any], path: str | Path) -> Path:
        """Explicitly write a caller-requested manifest; never writes by discovery."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target


__all__ = ["ManifestBuilder"]
