"""Campaign manifest and computational provenance records."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.campaign_provenance import file_sha256

from .campaign import CAMPAIGN_SCOPE, Campaign
from .campaign_events import utc_timestamp


@dataclass(frozen=True)
class CampaignManifest:
    """Portable manifest for a campaign and its produced artifacts."""

    campaign_id: str
    configuration_hash: str
    git_commit: str
    branch: str
    tag: str | None
    python: str
    package_versions: Mapping[str, str] = field(default_factory=dict)
    os_name: str = ""
    cpu: str = ""
    ram: str = "unknown"
    random_seeds: tuple[int, ...] = ()
    dataset_hashes: Mapping[str, str] = field(default_factory=dict)
    artifact_hashes: Mapping[str, str] = field(default_factory=dict)
    output_manifest: str | None = None
    timestamp: str = field(default_factory=utc_timestamp)
    scientific_scope: str = CAMPAIGN_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": 1,
            "campaign_id": self.campaign_id,
            "configuration_hash": self.configuration_hash,
            "git_commit": self.git_commit,
            "branch": self.branch,
            "tag": self.tag,
            "python": self.python,
            "package_versions": dict(sorted(self.package_versions.items())),
            "os": self.os_name,
            "cpu": self.cpu,
            "ram": self.ram,
            "random_seeds": list(self.random_seeds),
            "dataset_hashes": dict(sorted(self.dataset_hashes.items())),
            "artifact_hashes": dict(sorted(self.artifact_hashes.items())),
            "output_manifest": self.output_manifest,
            "timestamp": self.timestamp,
            "scientific_scope": self.scientific_scope,
        }

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target


def build_manifest(
    campaign: Campaign,
    *,
    datasets: Sequence[str | Path] = (),
    artifacts: Sequence[str | Path] = (),
    seeds: Sequence[int] = (),
    output_manifest: str | Path | None = None,
) -> CampaignManifest:
    """Collect provenance without importing or executing simulation packages."""

    return CampaignManifest(
        campaign_id=campaign.campaign_id,
        configuration_hash=campaign.configuration_hash,
        git_commit=_git_value(("rev-parse", "HEAD")),
        branch=_git_value(("branch", "--show-current")),
        tag=_git_tag(),
        python=platform.python_version(),
        package_versions=_package_versions(("drosophila-pd-flygym", "flygym", "mujoco", "numpy")),
        os_name=platform.platform(),
        cpu=platform.processor() or "unknown",
        ram=_ram(),
        random_seeds=tuple(int(seed) for seed in seeds),
        dataset_hashes={Path(path).as_posix(): file_sha256(path) for path in datasets if Path(path).is_file()},
        artifact_hashes={Path(path).as_posix(): file_sha256(path) for path in artifacts if Path(path).is_file()},
        output_manifest=Path(output_manifest).as_posix() if output_manifest else None,
    )


def _git_value(args: tuple[str, ...]) -> str:
    try:
        return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL, text=True).strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _git_tag() -> str | None:
    value = _git_value(("describe", "--tags", "--exact-match"))
    return None if value == "UNKNOWN" else value


def _package_versions(names: Sequence[str]) -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not-installed"
    return versions


def _ram() -> str:
    try:
        import psutil

        return str(psutil.virtual_memory().total)
    except Exception:
        return "unknown"


__all__ = ["CampaignManifest", "build_manifest"]
