"""Generate the additive Epic 12 release-engineering report package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.benchmarking import BENCHMARK_STAGES
from drosophila_pd.developer_tooling import ArchitectureSnapshot
from drosophila_pd.project_health import ProjectHealth
from drosophila_pd.release_engineering import ReleaseManifest, ReleaseNotesGenerator


def build_report(root: Path) -> dict:
    health = ProjectHealth(root).run()
    architecture = ArchitectureSnapshot(root).build()
    benchmark = {
        "status": "not_run",
        "reason": "No simulation or scientific workload is executed by release tooling.",
        "stages": [{"name": name, "status": "caller-supplied operation required"} for name in BENCHMARK_STAGES],
    }
    manifest = ReleaseManifest(root).build(health={"overall_pass": health["overall_pass"], "summary": health["summary"]})
    manifest["architecture"] = {
        "module_count": len(architecture["modules"]),
        "api_module_count": architecture["api"]["module_count"],
        "dependency_edge_count": len(architecture["dependencies"]["edges"]),
        "plugin_hook_count": len(architecture["hooks"]["hooks"]),
        "plugin_capability_count": len(architecture["hooks"]["capabilities"]),
    }
    manifest["benchmark"] = benchmark
    manifest["diagnostics"] = {
        "status": "available",
        "module": "drosophila_pd.debug_utils",
        "simulation_executed": False,
    }
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/release_engineering"))
    args = parser.parse_args()
    root = ROOT
    output = args.output if args.output.is_absolute() else root / args.output
    output.mkdir(parents=True, exist_ok=True)
    report = build_report(root)
    generator = ReleaseNotesGenerator()
    markdown = generator.to_markdown(report)
    markdown += "\n## Benchmark\n\nBenchmark stages are declared but require caller-supplied operations; this report does not run simulations.\n"
    (output / "release.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "release.md").write_text(markdown, encoding="utf-8")
    (output / "release.html").write_text(generator.to_html(report), encoding="utf-8")
    print(f"Generated release report in {output.relative_to(root).as_posix()}")


if __name__ == "__main__":
    main()
