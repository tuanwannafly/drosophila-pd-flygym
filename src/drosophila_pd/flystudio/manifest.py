from dataclasses import dataclass, field
from typing import List
import hashlib

@dataclass
class ManifestEntry:
    path: str
    checksum: str
    size_bytes: int

@dataclass
class Manifest:
    entries: List[ManifestEntry] = field(default_factory=list)

    def add_entry(self, path: str, data: bytes) -> None:
        checksum = hashlib.sha256(data).hexdigest()
        self.entries.append(ManifestEntry(path, checksum, len(data)))
