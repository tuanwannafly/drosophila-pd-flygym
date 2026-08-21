"""Release metadata and report primitives for the repository tooling layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html import escape
import subprocess
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class VersionMetadata:
    """Repository version and compatibility metadata."""

    version: str = "v1.0.0"
    canonical_branch: str = "main"
    source_commit: str | None = None
    python: str = "3.12"
    flygym: str = "2.1.0"
    mujoco: str = "3.9.0"
    generated_at: str | None = None

    @classmethod
    def from_repository(cls, root: str | Path, *, version: str = "v1.0.0") -> "VersionMetadata":
        root = Path(root)
        commit = _git_value(root, "rev-parse", "HEAD")
        return cls(
            version=version,
            source_commit=commit or None,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CompatibilityMatrix:
    """Describes the versions already recorded by the project."""

    def __init__(self, entries: list[Mapping[str, str]] | None = None) -> None:
        self.entries = [
            {"component": "Python", "tested_target": "3.12", "scope": "repository tests"},
            {"component": "FlyGym", "tested_target": "2.1.0", "scope": "Colab simulation checkpoints"},
            {"component": "MuJoCo", "tested_target": "3.9.0", "scope": "Colab simulation checkpoints"},
            {"component": "Web modules", "tested_target": "browser ESM", "scope": "web platform"},
        ] if entries is None else [dict(entry) for entry in entries]

    def as_list(self) -> list[dict[str, str]]:
        return [dict(entry) for entry in self.entries]


class MigrationNotes:
    """Stable migration guidance for the additive tooling layer."""

    def as_dict(self) -> dict[str, Any]:
        return {
            "backward_compatibility": True,
            "legacy_plugin_registry": "Preserved in web/experiment_workspace.js",
            "new_modules": [
                "drosophila_pd.release_engineering",
                "drosophila_pd.project_health",
                "drosophila_pd.developer_tooling",
                "drosophila_pd.debug_utils",
                "drosophila_pd.benchmarking",
            ],
            "scientific_pipeline": "Unchanged; no simulation or evidence regeneration is performed.",
        }


class ReleaseManifest:
    """Build a JSON-serializable inventory without modifying project files."""

    def __init__(self, root: str | Path, *, version: str = "v1.0.0") -> None:
        self.root = Path(root).resolve()
        self.metadata = VersionMetadata.from_repository(self.root, version=version)
        self.compatibility = CompatibilityMatrix()
        self.migration = MigrationNotes()

    def build(self, *, health: Mapping[str, Any] | None = None) -> dict[str, Any]:
        modules = _paths(self.root / "src", ("*.py",)) + _paths(self.root / "web", ("*.js",))
        return {
            "schema_version": 1,
            "version": self.metadata.version,
            "metadata": self.metadata.as_dict(),
            "build_information": {
                "source_root": ".",
                "python_module_count": len(_paths(self.root / "src", ("*.py",))),
                "web_module_count": len(_paths(self.root / "web", ("*.js",))),
                "script_count": len(_paths(self.root / "scripts", ("*.py", "*.mjs"))),
                "test_count": len(_paths(self.root / "tests", ("test_*.py",))),
                "module_examples": [path.relative_to(self.root).as_posix() for path in modules[:12]],
            },
            "compatibility": self.compatibility.as_list(),
            "migration": self.migration.as_dict(),
            "health": dict(health or {}),
            "scientific_boundary": "Release tooling only; no new scientific result or biological claim is generated.",
        }


class ReleaseNotesGenerator:
    """Render release metadata into Markdown or HTML."""

    def to_markdown(self, manifest: Mapping[str, Any]) -> str:
        metadata = manifest.get("metadata", {})
        build = manifest.get("build_information", {})
        lines = [
            f"# Release Engineering Report {manifest.get('version', '')}",
            "",
            "This report describes repository structure and developer tooling. It does not regenerate simulations or frozen evidence.",
            "",
            "## Version",
            "",
            f"- Source commit: `{metadata.get('source_commit', 'unknown')}`",
            f"- Canonical branch: `{metadata.get('canonical_branch', 'main')}`",
            f"- Python target: `{metadata.get('python', 'unknown')}`",
            f"- FlyGym target: `{metadata.get('flygym', 'unknown')}`",
            f"- MuJoCo target: `{metadata.get('mujoco', 'unknown')}`",
            "",
            "## Architecture",
            "",
            f"- Python modules: {build.get('python_module_count', 0)}",
            f"- Web modules: {build.get('web_module_count', 0)}",
            f"- Scripts: {build.get('script_count', 0)}",
            f"- Tests: {build.get('test_count', 0)}",
            "",
            "## Compatibility",
            "",
        ]
        lines.extend(f"- {entry['component']}: `{entry['tested_target']}` ({entry['scope']})" for entry in manifest.get("compatibility", []))
        lines.extend(["", "## Health", ""])
        health = manifest.get("health", {})
        lines.extend(f"- {name}: {value}" for name, value in health.items())
        lines.extend([
            "",
            "## Known Scope",
            "",
            manifest.get("scientific_boundary", "Release tooling only."),
            "",
            "## Migration",
            "",
            "The existing public APIs remain available. The release-engineering modules are additive.",
            "",
        ])
        return "\n".join(lines)

    def to_html(self, manifest: Mapping[str, Any]) -> str:
        markdown = self.to_markdown(manifest)
        paragraphs = "\n".join(f"<p>{escape(line)}</p>" for line in markdown.splitlines() if line.strip())
        return "<!doctype html>\n<html><head><meta charset=\"utf-8\"><title>Release Engineering Report</title></head><body>\n" + paragraphs + "\n</body></html>\n"


def _paths(directory: Path, patterns: tuple[str, ...]) -> list[Path]:
    if not directory.exists():
        return []
    return sorted({path for pattern in patterns for path in directory.rglob(pattern) if path.is_file()})


def _git_value(root: Path, *arguments: str) -> str:
    try:
        result = subprocess.run(["git", *arguments], cwd=root, check=False, capture_output=True, text=True)
    except OSError:
        return ""
    return result.stdout.strip() if result.returncode == 0 else ""
