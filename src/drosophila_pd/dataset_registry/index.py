"""Searchable in-memory index for registered dataset manifests."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .models import DatasetManifest


@dataclass
class DatasetIndex:
    """Index dataset metadata for browser-style search, filtering, and sorting."""

    manifests: list[DatasetManifest] = field(default_factory=list)

    def add(self, manifest: DatasetManifest) -> DatasetManifest:
        self.manifests = [item for item in self.manifests if item.dataset_id != manifest.dataset_id or item.root != manifest.root]
        self.manifests.append(manifest)
        return manifest

    def extend(self, manifests: Iterable[DatasetManifest]) -> None:
        for manifest in manifests:
            self.add(manifest)

    def search(
        self,
        query: str = "",
        *,
        dataset_type: str | None = None,
        status: str | None = None,
        tags: Sequence[str] = (),
        sort_by: str = "dataset_id",
    ) -> tuple[DatasetManifest, ...]:
        needle = query.casefold().strip()
        required_tags = {tag.casefold() for tag in tags}
        selected = []
        for manifest in self.manifests:
            metadata = manifest.metadata
            haystack = " ".join((manifest.dataset_id, manifest.dataset_type, manifest.status, *(metadata.tags if metadata else ())))
            if needle and needle not in haystack.casefold():
                continue
            if dataset_type and manifest.dataset_type != dataset_type:
                continue
            if status and manifest.status != status:
                continue
            observed_tags = {tag.casefold() for tag in metadata.tags} if metadata else set()
            if required_tags and not required_tags <= observed_tags:
                continue
            selected.append(manifest)
        return tuple(sorted(selected, key=lambda item: _sort_key(item, sort_by)))

    def as_dict(self) -> list[dict[str, object]]:
        return [manifest.as_dict() for manifest in self.manifests]


def _sort_key(manifest: DatasetManifest, field: str) -> str:
    if field == "status":
        return manifest.status
    if field == "dataset_type":
        return manifest.dataset_type
    if field == "version":
        return manifest.version.value
    return manifest.dataset_id


__all__ = ["DatasetIndex"]
