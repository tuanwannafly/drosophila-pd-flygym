"""Inspect curated FlyGym datasets without running simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.dataset_adapter import DatasetValidator, discover_datasets  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only FlyGym dataset discovery and validation.")
    parser.add_argument("command", choices=("discover", "validate", "report", "status", "summary"))
    parser.add_argument("--root", type=Path, default=None, help="Repository root.")
    parser.add_argument("--output", type=Path, default=None, help="Report directory or JSON path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = (args.root or ROOT).resolve()
    discovery = discover_datasets((root / "datasets", root / "research" / "datasets"))
    validator = DatasetValidator()
    validations = [validator.validate(dataset) for dataset in discovery.datasets]

    if args.command == "discover":
        payload = discovery.as_dict()
    elif args.command == "validate":
        payload = {
            "state": discovery.state,
            "overall_pass": bool(validations) and all(item.overall_pass for item in validations),
            "datasets": [item.as_dict() for item in validations],
            "missing_types": discovery.missing_types,
            "warnings": discovery.warnings,
        }
    elif args.command == "status":
        payload = {
            "state": discovery.state,
            "datasets_found": len(discovery.datasets),
            "datasets_missing": discovery.missing_types,
            "validation_passed": sum(item.overall_pass for item in validations),
            "validation_total": len(validations),
        }
    elif args.command == "summary":
        payload = {
            "state": discovery.state,
            "by_type": {dataset_type: sum(item.dataset_type == dataset_type for item in discovery.datasets) for dataset_type in ("healthy", "pd", "candidate", "control", "validation", "benchmark")},
            "missing_types": discovery.missing_types,
            "trajectory_files": sum(len(dataset.trajectory_files) for dataset in discovery.datasets),
            "frame_counts": {
                item.relative_path: item.frame_count
                for dataset in discovery.datasets
                for item in dataset.trajectory_files
                if item.frame_count is not None
            },
        }
    else:
        payload = _report_payload(discovery.as_dict(), validations)
        output_dir = (args.output or root / "results" / "dataset_adapter").resolve()
        if output_dir.suffix.casefold() == ".json":
            json_path = output_dir
            markdown_path = output_dir.with_suffix(".md")
        else:
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / "dataset_report.json"
            markdown_path = output_dir / "dataset_report.md"
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(_markdown_report(payload), encoding="utf-8")
        payload["report_json"] = json_path.as_posix()
        payload["report_markdown"] = markdown_path.as_posix()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _report_payload(discovery: dict[str, object], validations: list[object]) -> dict[str, object]:
    return {
        "report_version": 1,
        "state": discovery["state"],
        "overall_pass": bool(validations) and all(item.overall_pass for item in validations),
        "datasets_found": discovery["datasets"],
        "datasets_missing": discovery["missing_types"],
        "validation": [item.as_dict() for item in validations],
        "warnings": discovery["warnings"],
        "scientific_scope": "Read-only computational dataset intake; no simulation or biological validation claim.",
    }


def _markdown_report(payload: dict[str, object]) -> str:
    lines = [
        "# Dataset Report",
        "",
        f"- State: `{payload['state']}`",
        f"- Overall validation pass: `{payload['overall_pass']}`",
        "- Scope: read-only computational dataset intake.",
        "",
        "## Dataset Inventory",
        "",
        f"- Found: `{len(payload['datasets_found'])}`",
        f"- Missing types: `{', '.join(payload['datasets_missing']) or 'none'}`",
        "",
        "## Validation",
        "",
    ]
    rows = payload["validation"]
    if rows:
        lines.extend(f"- `{item['dataset_id']}`: `{item['overall_pass']}`" for item in rows)
    else:
        lines.append("- No dataset was available for validation.")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
