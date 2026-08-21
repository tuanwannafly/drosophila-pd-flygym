"""CLI for Milestone 3 research administration and reproducibility tooling.

All commands are metadata/artifact operations.  No command runs FlyGym,
MuJoCo, a simulation, or fabricates a rollout.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.automation import (  # noqa: E402
    ArtifactManager,
    BenchmarkCenter,
    DeveloperToolkit,
    PublicationBuilder,
    ResearchAutomationPlatform,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (
        ("build-project", "write an automation manifest"),
        ("generate-manifest", "write an automation manifest"),
        ("health-check", "run static project-health checks"),
        ("run-validation", "run non-simulation repository validation checks"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--output", type=Path)

    benchmark = subparsers.add_parser("benchmark", help="report benchmark scope without an injected workload")
    benchmark.add_argument("--output", type=Path)
    benchmark.add_argument("--iterations", type=int, default=1)

    bundle = subparsers.add_parser("create-bundle", help="create an empty metadata/artifact bundle layout")
    bundle.add_argument("--output", type=Path, required=True)

    publication = subparsers.add_parser("export-publication", help="package caller-provided publication assets")
    publication.add_argument("--output", type=Path, required=True)
    publication.add_argument("--asset", action="append", default=[], metavar="SECTION=PATH")

    developer = subparsers.add_parser("developer", help="inspect project developer metadata")
    developer.add_argument("kind", choices=("project-doctor", "dependency-inspector", "architecture-browser", "api-explorer", "test-explorer", "performance-explorer"))
    developer.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    platform = ResearchAutomationPlatform(args.root)
    output = _resolve_output(args.root, getattr(args, "output", None))

    if args.command in {"build-project", "generate-manifest"}:
        path = platform.write_manifest(output or platform.output_root / "automation_manifest.json")
        return _print({"overall_pass": path.is_file(), "output": path.as_posix()})
    if args.command in {"health-check", "run-validation"}:
        report = platform.health_check()
        if output:
            _write_json(output, report)
        return _print(report, exit_code=0 if report["overall_pass"] else 1)
    if args.command == "benchmark":
        report = BenchmarkCenter().not_run_report()
        if output:
            _write_json(output, report)
        return _print(report)
    if args.command == "create-bundle":
        manager = ArtifactManager(args.output)
        layout = manager.prepare()
        manifest = manager.write_manifest()
        return _print({"overall_pass": manifest.is_file(), "layout": _paths(layout), "manifest": manifest.as_posix()})
    if args.command == "export-publication":
        builder = PublicationBuilder(args.output)
        for asset in args.asset:
            section, separator, source = asset.partition("=")
            if not separator:
                raise SystemExit("--asset must use SECTION=PATH")
            builder.register(source, section)
        manifest = builder.build(metadata={"asset_count": len(builder.assets)})
        return _print({"overall_pass": manifest.is_file(), "manifest": manifest.as_posix(), "asset_count": len(builder.assets)})
    if args.command == "developer":
        toolkit = DeveloperToolkit(args.root)
        reports = {
            "project-doctor": platform.health_check,
            "dependency-inspector": toolkit.dependency_report,
            "architecture-browser": toolkit.architecture_report,
            "api-explorer": toolkit.api_report,
            "test-explorer": toolkit.test_report,
            "performance-explorer": toolkit.performance_report,
        }
        report = reports[args.kind]()
        if output:
            _write_json(output, report)
        return _print(report)
    return 2


def _resolve_output(root: Path, value: Path | None) -> Path | None:
    if value is None:
        return None
    return value if value.is_absolute() else root / value


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _paths(paths: dict[str, Path]) -> dict[str, str]:
    return {key: path.as_posix() for key, path in sorted(paths.items())}


def _print(payload: object, *, exit_code: int = 0) -> int:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
