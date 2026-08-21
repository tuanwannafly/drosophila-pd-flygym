"""Service and operational-resource registries for the Research Kernel."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


@dataclass
class ServiceRecord:
    name: str
    service: Any = field(repr=False, default=None)
    available: bool = False
    module: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "module": self.module,
            "metadata": dict(self.metadata),
        }


class ServiceRegistry:
    """Explicit registry of existing subsystem APIs and their availability."""

    def __init__(self) -> None:
        self._services: dict[str, ServiceRecord] = {}

    def register(
        self,
        name: str,
        service: Any = None,
        *,
        module: str = "",
        available: bool | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> ServiceRecord:
        record = ServiceRecord(
            name=str(name),
            service=service,
            available=bool(service is not None) if available is None else bool(available),
            module=module,
            metadata=dict(metadata or {}),
        )
        self._services[record.name] = record
        return record

    def get(self, name: str) -> Any:
        record = self._services[str(name)]
        if not record.available or record.service is None:
            raise LookupError(f"Service is not available: {name}")
        return record.service

    def record(self, name: str) -> ServiceRecord:
        return self._services[str(name)]

    def names(self) -> tuple[str, ...]:
        return tuple(self._services)

    def as_dict(self) -> dict[str, Any]:
        return {"registry_version": 1, "services": [item.as_dict() for item in self._services.values()]}

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target


@dataclass(frozen=True)
class ResourceRecord:
    category: str
    path: str
    exists: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "path": self.path,
            "exists": self.exists,
            "metadata": dict(self.metadata),
        }


class ResourceManager:
    """Track operational resources without reading rollout arrays."""

    CATEGORIES = ("datasets", "sessions", "artifacts", "reports", "figures", "tables", "bundles")

    def __init__(self) -> None:
        self._resources: list[ResourceRecord] = []

    def register(self, category: str, path: str | Path, *, metadata: Mapping[str, Any] | None = None) -> ResourceRecord:
        record = ResourceRecord(category=str(category), path=Path(path).as_posix(), metadata=dict(metadata or {}))
        self._resources = [item for item in self._resources if (item.category, item.path) != (record.category, record.path)]
        self._resources.append(record)
        return record

    def register_missing(self, category: str, path: str | Path, *, metadata: Mapping[str, Any] | None = None) -> ResourceRecord:
        record = ResourceRecord(category=str(category), path=Path(path).as_posix(), exists=False, metadata=dict(metadata or {}))
        self._resources = [item for item in self._resources if (item.category, item.path) != (record.category, record.path)]
        self._resources.append(record)
        return record

    def records(self, category: str | None = None) -> list[ResourceRecord]:
        return [item for item in self._resources if category is None or item.category == category]

    def as_dict(self) -> dict[str, Any]:
        return {"resource_schema_version": 1, "resources": [item.as_dict() for item in self._resources]}

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return target


__all__ = ["ResourceManager", "ResourceRecord", "ServiceRecord", "ServiceRegistry"]
