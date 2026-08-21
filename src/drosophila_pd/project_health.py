"""Static project-health checks for release and maintenance workflows."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HealthCheck:
    name: str
    status: str
    details: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ProjectHealth:
    """Run conservative static checks without importing or executing research code."""

    DEFAULT_REQUIRED = (
        "src/drosophila_pd/__init__.py",
        "web/experiment_workspace.js",
        "web/plugin_platform.js",
        "web/integration_workflow.js",
        "web/verification_suite.js",
        "tests/test_web_experiment_workspace_contract.py",
    )

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def run(self, required: tuple[str, ...] | None = None) -> dict[str, Any]:
        checks = [
            self.check_missing_modules(required or self.DEFAULT_REQUIRED),
            self.check_duplicate_modules(),
            self.check_unused_imports(),
            self.check_unused_exports(),
            self.check_dead_plugins(),
            self.check_circular_dependencies(),
            self.check_configuration_consistency(),
            self.check_documentation_coverage(),
        ]
        failures = sum(check.status == "FAIL" for check in checks)
        return {
            "overall_pass": failures == 0,
            "checks": {check.name: check.as_dict() for check in checks},
            "summary": {
                "pass": sum(check.status == "PASS" for check in checks),
                "info": sum(check.status == "INFO" for check in checks),
                "warn": sum(check.status == "WARN" for check in checks),
                "fail": failures,
            },
        }

    def check_missing_modules(self, required: tuple[str, ...]) -> HealthCheck:
        missing = tuple(path for path in required if not (self.root / path).is_file())
        return HealthCheck("missing_modules", "FAIL" if missing else "PASS", missing or ("All required release modules exist.",))

    def check_duplicate_modules(self) -> HealthCheck:
        candidates = [path for base in (self.root / "src", self.root / "web") for path in base.rglob("*") if path.is_file() and path.suffix in {".py", ".js"} and path.stem != "__init__"]
        by_name: dict[str, list[str]] = {}
        for path in candidates:
            by_name.setdefault(path.stem, []).append(path.relative_to(self.root).as_posix())
        duplicates = tuple(f"{name}: {', '.join(paths)}" for name, paths in sorted(by_name.items()) if len(paths) > 1)
        return HealthCheck("duplicate_modules", "INFO" if duplicates else "PASS", duplicates or ("No duplicate non-package module names found.",))

    def check_unused_imports(self) -> HealthCheck:
        candidates: list[str] = []
        for path in (self.root / "src").rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        bound = alias.asname or alias.name.split(".")[0]
                        if bound not in names - {bound}:
                            candidates.append(f"{path.relative_to(self.root).as_posix()}: {bound}")
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        if alias.name == "*":
                            continue
                        bound = alias.asname or alias.name
                        if bound not in names - {bound}:
                            candidates.append(f"{path.relative_to(self.root).as_posix()}: {bound}")
        return HealthCheck("unused_imports", "INFO" if candidates else "PASS", tuple(candidates[:50]) or ("No heuristic unused-import candidates found.",))

    def check_unused_exports(self) -> HealthCheck:
        candidates: list[str] = []
        for path in (self.root / "src").rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            for node in tree.body:
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                            defined = {item.name for item in tree.body if isinstance(item, (ast.FunctionDef, ast.ClassDef))}
                            defined.update(target.id for item in tree.body if isinstance(item, ast.Assign) for target in item.targets if isinstance(target, ast.Name))
                            for item in node.value.elts:
                                if isinstance(item, ast.Constant) and item.value not in defined:
                                    candidates.append(f"{path.relative_to(self.root).as_posix()}: {item.value}")
        return HealthCheck("unused_exports", "INFO" if candidates else "PASS", tuple(candidates[:50]) or ("No stale __all__ entries found.",))

    def check_dead_plugins(self) -> HealthCheck:
        directory = self.root / "web" / "plugins"
        if not directory.exists():
            return HealthCheck("dead_plugins", "INFO", ("No plugin example directory exists.",))
        invalid = []
        for path in sorted(directory.glob("*.js")):
            text = path.read_text(encoding="utf-8")
            if "manifest" not in text or "run(input, context)" not in text:
                invalid.append(path.relative_to(self.root).as_posix())
        platform = self.root / "web" / "plugin_platform.js"
        if not platform.is_file():
            invalid.append("web/plugin_platform.js")
        return HealthCheck("dead_plugins", "FAIL" if invalid else "PASS", tuple(invalid) or ("Plugin examples have a manifest and run boundary.",))

    def check_circular_dependencies(self) -> HealthCheck:
        graph = self._python_dependency_graph()
        cycles = tuple(" -> ".join(cycle) for cycle in _find_cycles(graph))
        return HealthCheck("circular_dependencies", "FAIL" if cycles else "PASS", cycles or ("No local Python dependency cycles found.",))

    def check_configuration_consistency(self) -> HealthCheck:
        configs = list((self.root / "configs").rglob("*.yaml")) + list((self.root / "configs").rglob("*.yml")) + list((self.root / "configs").rglob("*.json"))
        invalid = []
        for path in configs:
            if not path.read_text(encoding="utf-8").strip():
                invalid.append(path.relative_to(self.root).as_posix())
        return HealthCheck("configuration_consistency", "FAIL" if invalid else "PASS", tuple(invalid) or (f"Checked {len(configs)} non-empty configuration files.",))

    def check_documentation_coverage(self) -> HealthCheck:
        docs = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in (self.root / "docs").rglob("*.md"))
        modules = [path.stem for path in (self.root / "src" / "drosophila_pd").rglob("*.py") if path.stem != "__init__"]
        uncovered = tuple(module for module in modules if module not in docs)
        return HealthCheck("documentation_coverage", "INFO" if uncovered else "PASS", tuple(uncovered[:50]) or ("All Python module names appear in documentation.",))

    def _python_dependency_graph(self) -> dict[str, set[str]]:
        package = self.root / "src" / "drosophila_pd"
        modules = {path.relative_to(self.root / "src").with_suffix("").as_posix().replace("/", "."): path for path in package.rglob("*.py")}
        graph = {name: set() for name in modules}
        for name, path in modules.items():
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                imported = None
                if isinstance(node, ast.Import):
                    imported = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported = [node.module]
                for target in imported or []:
                    if target in modules and target != name:
                        graph[name].add(target)
        return graph


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    found: list[list[str]] = []
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in visiting:
            found.append(visiting[visiting.index(node):] + [node])
            return
        if node in visited:
            return
        visiting.append(node)
        for target in graph.get(node, ()):
            visit(target)
        visiting.pop()
        visited.add(node)

    for node in graph:
        visit(node)
    return found
