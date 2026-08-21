import json
from dataclasses import dataclass, field, asdict
from typing import Dict, Any

@dataclass
class AssetManifest:
    """JSON serializable manifest of assets."""
    version: str = "1.0"
    entries: Dict[str, Any] = field(default_factory=dict)

    def serialize(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def deserialize(cls, json_str: str) -> 'AssetManifest':
        data = json.loads(json_str)
        return cls(**data)
