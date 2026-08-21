"""Provenance helpers for v2 research campaigns."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class CampaignProvenance:
    """Immutable provenance record for a campaign or artifact set."""

    campaign_id: str
    git_commit: str
    configuration_hash: str
    artifact_hashes: Mapping[str, str] = field(default_factory=dict)
    dataset_hash: str | None = None
    software_versions: Mapping[str, str] = field(default_factory=dict)
    seeds: tuple[int, ...] = ()
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    environment: Mapping[str, str] = field(default_factory=dict)
    scientific_scope: str = (
        "Computational provenance only; no biological validation or Parkinson's "
        "disease claim."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "campaign_id": self.campaign_id,
            "git_commit": self.git_commit,
            "configuration_hash": self.configuration_hash,
            "dataset_hash": self.dataset_hash,
            "artifact_hashes": dict(sorted(self.artifact_hashes.items())),
            "software_versions": dict(sorted(self.software_versions.items())),
            "seeds": [int(seed) for seed in self.seeds],
            "timestamp": self.timestamp,
            "environment": dict(sorted(self.environment.items())),
            "scientific_scope": self.scientific_scope,
        }


def stable_hash(payload: Any) -> str:
    """Return a stable SHA-256 hash for a JSON-compatible payload."""

    return hashlib.sha256(json.dumps(_jsonable(payload), sort_keys=True).encode("utf-8")).hexdigest()


def file_sha256(path: str | Path) -> str:
    """Compute the SHA-256 hash of a file."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def directory_manifest(root: str | Path) -> dict[str, str]:
    """Hash all files below a directory using POSIX-style relative paths."""

    base = Path(root)
    if not base.exists():
        return {}
    return {
        path.relative_to(base).as_posix(): file_sha256(path)
        for path in sorted(base.rglob("*"))
        if path.is_file()
    }


def collect_campaign_provenance(
    *,
    campaign_id: str,
    config: Mapping[str, Any],
    artifacts: Sequence[str | Path] = (),
    seeds: Sequence[int] = (),
    dataset_path: str | Path | None = None,
) -> CampaignProvenance:
    """Collect reproducibility metadata without importing simulation packages."""

    artifact_hashes = {Path(path).as_posix(): file_sha256(path) for path in artifacts if Path(path).is_file()}
    return CampaignProvenance(
        campaign_id=campaign_id,
        git_commit=current_git_commit(),
        configuration_hash=stable_hash(config),
        artifact_hashes=artifact_hashes,
        dataset_hash=file_sha256(dataset_path) if dataset_path and Path(dataset_path).is_file() else None,
        software_versions={"python": platform.python_version()},
        seeds=tuple(int(seed) for seed in seeds),
        environment={"platform": platform.platform(), "executable": sys.executable},
    )


def write_provenance_manifest(provenance: CampaignProvenance, output_path: str | Path) -> Path:
    """Write provenance JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(provenance.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def current_git_commit() -> str:
    """Return the current git commit, or UNKNOWN outside git."""

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "UNKNOWN"


def _jsonable(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


__all__ = [
    "CampaignProvenance",
    "collect_campaign_provenance",
    "current_git_commit",
    "directory_manifest",
    "file_sha256",
    "stable_hash",
    "write_provenance_manifest",
]
