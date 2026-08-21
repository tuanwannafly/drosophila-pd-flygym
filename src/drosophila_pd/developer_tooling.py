"""Repository explorers used by developers and release reports."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import re
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModuleRecord:
    path: str
    kind: str
    exports: tuple[str, ...] = ()
    imports: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ModuleIndex:
    """Index Python and web modules without importing them."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def build(self) -> list[dict[str, Any]]:
        records = []
        for path in sorted((self.root / "src").rglob("*.py")):
            records.append(self._python_record(path))
        for path in sorted((self.root / "web").rglob("*.js")):
            records.append(self._javascript_record(path))
        return [record.as_dict() for record in records]

    def _python_record(self, path: Path) -> ModuleRecord:
        text = path.read_text(encoding="utf-8")
        exports: list[str] = []
        imports: list[str] = []
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return ModuleRecord(self._relative(path), "python", ("<syntax-error>",), ())
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                exports.append(node.name)
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return ModuleRecord(self._relative(path), "python", tuple(sorted(set(exports))), tuple(sorted(set(imports))))

    def _javascript_record(self, path: Path) -> ModuleRecord:
        text = path.read_text(encoding="utf-8")
        exports = re.findall(r"export\s+(?:class|function|const|let|var)\s+([A-Za-z_$][\w$]*)", text)
        imports = re.findall(r"from\s+['\"]([^'\"]+)['\"]", text)
        return ModuleRecord(self._relative(path), "javascript", tuple(sorted(set(exports))), tuple(sorted(set(imports))))

    def _relative(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()


class APIExplorer:
    """Produce a public API index from a module index."""

    def __init__(self, module_index: ModuleIndex) -> None:
        self.module_index = module_index

    def explore(self) -> dict[str, Any]:
        modules = self.module_index.build()
        return {
            "module_count": len(modules),
            "modules": [
                {"path": module["path"], "kind": module["kind"], "exports": module["exports"]}
                for module in modules
                if module["exports"]
            ],
        }


class DependencyGraphGenerator:
    """Generate a relative-import graph and Graphviz DOT representation."""

    def __init__(self, module_index: ModuleIndex) -> None:
        self.module_index = module_index

    def build(self) -> dict[str, Any]:
        records = self.module_index.build()
        known = {record["path"] for record in records}
        edges = []
        for record in records:
            for imported in record["imports"]:
                if imported.startswith("."):
                    edges.append({"source": record["path"], "import": imported, "resolved": self._resolve(record["path"], imported, known)})
        return {"nodes": sorted(known), "edges": edges}

    def to_dot(self) -> str:
        graph = self.build()
        lines = ["digraph fly_studio {", *[f'  "{node}";' for node in graph["nodes"]]]
        lines.extend(f'  "{edge["source"]}" -> "{edge["resolved"]}";' for edge in graph["edges"] if edge["resolved"])
        lines.append("}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _resolve(source: str, imported: str, known: set[str]) -> str | None:
        base = Path(source).parent
        candidate = (base / imported.removeprefix("./")).with_suffix(".js").as_posix()
        return candidate if candidate in known else None


class HookExplorer:
    """Inspect the declared hook and capability contract."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def explore(self) -> dict[str, Any]:
        platform = self.root / "web" / "plugin_platform.js"
        text = platform.read_text(encoding="utf-8") if platform.exists() else ""
        hooks = re.findall(r"'((?:on)[A-Z][A-Za-z]+)'", text.split("export const PLUGIN_CAPABILITIES", 1)[0])
        capability_text = text.split("export const PLUGIN_CAPABILITIES", 1)[-1]
        capabilities = re.findall(r"'([a-z]+)'", capability_text.split("]);", 1)[0] if "]);" in capability_text else "")
        examples = sorted(path.relative_to(self.root).as_posix() for path in (self.root / "web" / "plugins").glob("*.js")) if (self.root / "web" / "plugins").exists() else []
        return {"hooks": sorted(set(hooks)), "capabilities": sorted(set(capabilities)), "example_plugins": examples}


class PluginRegistryViewer:
    """Render a serializable view of either plugin registry API."""

    def snapshot(self, registry: Any) -> list[dict[str, Any]]:
        if hasattr(registry, "list"):
            return registry.list()
        return []


class ArchitectureSnapshot:
    """Combine module, API, dependency, hook, and plugin views."""

    def __init__(self, root: str | Path) -> None:
        self.module_index = ModuleIndex(root)
        self.api = APIExplorer(self.module_index)
        self.dependencies = DependencyGraphGenerator(self.module_index)
        self.hooks = HookExplorer(root)

    def build(self, registry: Any | None = None) -> dict[str, Any]:
        snapshot: dict[str, Any] = {
            "modules": self.module_index.build(),
            "api": self.api.explore(),
            "dependencies": self.dependencies.build(),
            "hooks": self.hooks.explore(),
        }
        if registry is not None:
            snapshot["plugins"] = PluginRegistryViewer().snapshot(registry)
        return snapshot
