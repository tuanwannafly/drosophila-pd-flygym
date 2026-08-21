from dataclasses import dataclass, field
from typing import List

@dataclass
class PipelineReport:
    project_name: str
    is_valid: bool = False
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def log_error(self, err: str):
        self.errors.append(err)
        self.is_valid = False

    def log_warning(self, warn: str):
        self.warnings.append(warn)
