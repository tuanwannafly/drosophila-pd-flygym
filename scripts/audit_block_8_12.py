#!/usr/bin/env python
"""Run the reproducible, non-mutating Block 8.12 audit."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.anatomy.audit import (  # noqa: E402
    AuditError,
    build_block_8_12_report,
    build_unavailable_report,
    instantiate_neuromechfly,
    runtime_environment,
    write_json_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Block 8.12 pre-materialization anatomy audit."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for a small JSON report, for example results/baseline/block_8_12_audit.json.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print("Block 8.12 pre-materialization audit")
    print("Environment:")
    for key, value in runtime_environment().items():
        print(f"  {key}: {value}")

    try:
        fly = instantiate_neuromechfly()
        report = build_block_8_12_report(fly, repo_root=REPO_ROOT)
    except Exception as exc:
        report = build_unavailable_report(exc, repo_root=REPO_ROOT)
        print("\nLOCAL EXECUTION = NOT VERIFIED")
        print(f"{type(exc).__name__}: {exc}")
        if args.output is not None:
            write_json_report(report, args.output)
            print(f"\nWrote JSON report: {args.output}")
        return 2

    print("\nObserved:")
    for key, value in report["observed"].items():
        if key.endswith("_names") or key == "jointdof_first_names":
            print(f"  {key}: {value[:5]}{' ...' if len(value) > 5 else ''}")
        else:
            print(f"  {key}: {value}")

    print("\nChecks:")
    for name, check in report["checks"].items():
        status = "PASS" if check["pass"] else "FAIL"
        print(f"  {status} {name}: observed={check['observed']} expected={check['expected']}")

    overall_status = "PASS" if report["overall_pass"] else "FAIL"
    print(f"\nOverall: {overall_status}")
    print(report["scientific_scope"])

    if args.output is not None:
        write_json_report(report, args.output)
        print(f"\nWrote JSON report: {args.output}")

    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
