"""Dataset building utilities for completed v2 campaigns."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from drosophila_pd.behavior_platform.ai_dataset import (
    BehaviorDataset,
    BehaviorSample,
    DatasetExporter,
    build_behavior_index,
    create_dataset_manifest,
)


@dataclass(frozen=True)
class CampaignDatasetBuilder:
    """Build versioned behavior datasets from completed campaign results."""

    dataset_id: str
    version: str = "v2.campaign_dataset.1"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def build(self, results: Sequence[Mapping[str, Any]]) -> BehaviorDataset:
        samples = tuple(_sample_from_result(index, result) for index, result in enumerate(results))
        return BehaviorDataset(
            dataset_id=self.dataset_id,
            version=self.version,
            samples=samples,
            metadata={
                "source": "research_campaign",
                "scientific_scope": "Computational dataset only; no biological validation claim.",
                **dict(self.metadata),
            },
        )

    def export_package(
        self,
        results: Sequence[Mapping[str, Any]],
        output_dir: str | Path,
        *,
        formats: Sequence[str] = ("json", "csv", "npz"),
    ) -> dict[str, Path]:
        dataset = self.build(results)
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        files: dict[str, Path] = {}
        for fmt in formats:
            files[f"dataset_{fmt}"] = DatasetExporter.export(dataset, output / f"{self.dataset_id}.{fmt}", format=fmt)
        manifest = create_dataset_manifest(dataset)
        files["manifest"] = output / "dataset_manifest.json"
        files["manifest"].write_text(json.dumps(manifest.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
        index = build_behavior_index(dataset)
        files["index"] = output / "dataset_index.json"
        files["index"].write_text(json.dumps(index.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return files


def merge_campaign_datasets(
    datasets: Sequence[BehaviorDataset],
    *,
    dataset_id: str,
    version: str = "v2.campaign_dataset.merged",
) -> BehaviorDataset:
    """Merge campaign datasets while preserving sample order."""

    samples: list[BehaviorSample] = []
    for dataset in datasets:
        samples.extend(dataset.samples)
    seen: set[str] = set()
    for sample in samples:
        if sample.sample_id in seen:
            raise ValueError(f"duplicate sample_id in merged dataset: {sample.sample_id}")
        seen.add(sample.sample_id)
    return BehaviorDataset(
        dataset_id=dataset_id,
        version=version,
        samples=tuple(samples),
        metadata={"source_dataset_ids": [dataset.dataset_id for dataset in datasets]},
    )


def validate_campaign_dataset(dataset: BehaviorDataset) -> dict[str, Any]:
    """Validate finite, indexable campaign dataset structure."""

    manifest = create_dataset_manifest(dataset)
    index = build_behavior_index(dataset)
    return {
        "dataset_id": dataset.dataset_id,
        "sample_count": len(dataset.samples),
        "manifest_sample_count": manifest.sample_count,
        "index_sample_count": len(index.sample_ids),
        "unique_sample_ids": len(set(index.sample_ids)) == len(index.sample_ids),
        "overall_pass": manifest.sample_count == len(index.sample_ids) and len(set(index.sample_ids)) == len(index.sample_ids),
    }


def load_campaign_results(paths: Sequence[str | Path]) -> tuple[Mapping[str, Any], ...]:
    """Load campaign result JSON files."""

    return tuple(json.loads(Path(path).read_text(encoding="utf-8")) for path in paths)


def _sample_from_result(index: int, result: Mapping[str, Any]) -> BehaviorSample:
    experiment = result.get("experiment", result.get("plan", {}))
    arrays = dict(result.get("arrays", {}))
    metrics = dict(result.get("metrics", {}))
    if not arrays and "thorax_positions" in result:
        arrays["thorax_positions"] = result["thorax_positions"]
    if not arrays:
        arrays["metrics_vector"] = [float(value) for value in metrics.values() if isinstance(value, (int, float))]
    sample_id = str(result.get("sample_id") or experiment.get("experiment_id") or f"campaign_sample_{index:04d}")
    condition = str(result.get("condition") or experiment.get("role") or result.get("condition_id") or "Unknown")
    metadata = {
        "experiment_id": experiment.get("experiment_id"),
        "seed": experiment.get("seed", result.get("seed")),
        "replicate": experiment.get("replicate", result.get("replicate")),
        "metrics": metrics,
        **dict(result.get("metadata", {})),
    }
    return BehaviorSample(sample_id=sample_id, condition=condition, arrays=arrays, labels=(condition,), metadata=metadata)


__all__ = [
    "CampaignDatasetBuilder",
    "load_campaign_results",
    "merge_campaign_datasets",
    "validate_campaign_dataset",
]
