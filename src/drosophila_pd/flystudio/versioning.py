from dataclasses import dataclass

@dataclass
class Version:
    major: int
    minor: int
    patch: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        parts = version_str.split('.')
        if len(parts) != 3:
            return cls(1, 0, 0)
        try:
            return cls(int(parts[0]), int(parts[1]), int(parts[2]))
        except ValueError:
            return cls(1, 0, 0)
