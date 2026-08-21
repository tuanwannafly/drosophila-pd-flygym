from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class AssetCache:
    """LRU abstraction for asset caching."""
    max_memory_mb: float = 1024.0
    current_memory_mb: float = 0.0
    _cache: Dict[str, Any] = field(default_factory=dict)
    _usage_order: list = field(default_factory=list)

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            self._usage_order.remove(key)
            self._usage_order.append(key)
            return self._cache[key]
        return None

    def put(self, key: str, asset: Any, size_mb: float = 1.0) -> None:
        while self.current_memory_mb + size_mb > self.max_memory_mb and self._usage_order:
            lru_key = self._usage_order.pop(0)
            del self._cache[lru_key]
            self.current_memory_mb -= 1.0

        self._cache[key] = asset
        self._usage_order.append(key)
        self.current_memory_mb += size_mb
