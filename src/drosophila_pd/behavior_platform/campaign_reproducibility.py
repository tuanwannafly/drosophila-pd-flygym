"""Replay and integrity checks for v2 research campaigns."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.ai_dataset import DatasetLoader, DatasetManifest, verify_dataset_integrity
from drosophila_pd.behavior_platform.campaign import CampaignConfig, create_campaign
from drosophila_pd.behavior_platform.campaign_provenance import file_sha256, stable_hash


def replay_campaign_plan(config: CampaignConfig) -> dict[str, Any]:
    """Reconstruct a campaign plan and return its deterministic identity."""

    campaign = create_campaign(config)
    return {
        "campaign_id": config.campaign_id,
        "config_hash": campaign.manifest.config_hash,
        "experiment_count": len(campaign.experiments),
        "experiment_ids": [plan.experiment_id for plan in campaign.experiments],
    }


def verify_campaign_replay(config: CampaignConfig, expected_manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Verify that a config reproduces an expected campaign manifest."""

    replay = replay_campaign_plan(config)
    passed = (
        replay["config_hash"] == expected_manifest.get("config_hash")
        and replay["experiment_ids"] == list(expected_manifest.get("experiment_ids", ()))
    )
    return {"overall_pass": bool(passed), "replay": replay}


def verify_artifact_hashes(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Verify artifact hashes from a manifest mapping."""

    rows = []
    for path_text, expected in _artifact_rows(manifest):
        path = Path(path_text)
        exists = path.is_file()
        observed = file_sha256(path) if exists else None
        rows.append(
            {
                "path": path_text,
                "exists": exists,
                "expected_sha256": expected,
                "observed_sha256": observed,
                "pass": exists and observed == expected,
            }
        )
    return {"overall_pass": all(row["pass"] for row in rows), "artifacts": rows}


def verify_dataset_package(dataset_path: str | Path, manifest_path: str | Path) -> dict[str, Any]:
    """Verify a dataset file against a dataset manifest."""

    dataset = DatasetLoader.load(dataset_path)
    manifest_data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    manifest = DatasetManifest(
        dataset_id=str(manifest_data["dataset_id"]),
        version=str(manifest_data["version"]),
        sample_count=int(manifest_data["sample_count"]),
        checksums=dict(manifest_data.get("checksums", {})),
        metadata=dict(manifest_data.get("metadata", {})),
    )
    return {
        "dataset_path": Path(dataset_path).as_posix(),
        "manifest_path": Path(manifest_path).as_posix(),
        "overall_pass": verify_dataset_integrity(dataset, manifest),
    }


def verify_manifest_signature(manifest: Mapping[str, Any], expected_hash: str | None = None) -> dict[str, Any]:
    """Compute and optionally validate a manifest content hash."""

    observed = stable_hash(manifest)
    return {
        "manifest_hash": observed,
        "expected_hash": expected_hash,
        "overall_pass": expected_hash is None or observed == expected_hash,
    }


def _artifact_rows(manifest: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    artifacts = manifest.get("artifacts", manifest.get("artifact_hashes", manifest))
    rows: list[tuple[str, str]] = []
    if isinstance(artifacts, Mapping):
        for key, value in artifacts.items():
            if isinstance(value, Mapping):
                path = str(value.get("path", key))
                checksum = str(value.get("sha256", ""))
            else:
                path = str(key)
                checksum = str(value)
            rows.append((path, checksum))
    elif isinstance(artifacts, Sequence):
        for item in artifacts:
            if isinstance(item, Mapping):
                rows.append((str(item.get("path", "")), str(item.get("sha256", ""))))
    return tuple(rows)


__all__ = [
    "replay_campaign_plan",
    "verify_artifact_hashes",
    "verify_campaign_replay",
    "verify_dataset_package",
    "verify_manifest_signature",
]
