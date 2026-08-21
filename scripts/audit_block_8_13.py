#!/usr/bin/env python
"""Run the read-only Block 8.13 orientation audit."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.anatomy.orientation import (  # noqa: E402
    build_block_8_13_orientation_report,
    build_block_8_13_unavailable_report,
    instantiate_neuromechfly,
    runtime_environment,
    write_json_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Block 8.13 read-only orientation audit."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional path for a small JSON report, for example "
            "results/baseline/block_8_13_orientation.json."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print("Block 8.13 read-only orientation audit")
    print("Environment:")
    for key, value in runtime_environment().items():
        print(f"  {key}: {value}")

    try:
        fly = instantiate_neuromechfly()
        report = build_block_8_13_orientation_report(fly, repo_root=REPO_ROOT)
    except Exception as exc:
        report = build_block_8_13_unavailable_report(exc, repo_root=REPO_ROOT)
        print("\nLOCAL EXECUTION = NOT VERIFIED")
        print(f"{type(exc).__name__}: {exc}")
        if args.output is not None:
            write_json_report(report, args.output)
            print(f"\nWrote JSON report: {args.output}")
        return 2

    observed = report["observed"]
    print("\nFly class:")
    print(f"  {observed['fly_type']}")

    print("\nMRO:")
    for item in observed["fly_mro"]:
        print(f"  {item}")

    print("\nSafety:")
    print(f"  skeleton_before_is_none: {observed['skeleton_before_is_none']}")
    print(f"  skeleton_after_is_none: {observed['skeleton_after_is_none']}")

    print("\nMJCF/root objects:")
    for item in observed["mjcf_root_objects"]:
        if item["present"] and not item["is_none"]:
            print(f"  {item['name']}: {item['type']}")

    print("\nMapping containers:")
    for name, summary in sorted(observed["mapping_containers"].items()):
        nested = summary["nested_total_length"]
        if nested is None:
            print(f"  {name}: length={summary['length']}")
        else:
            print(
                f"  {name}: length={summary['length']} "
                f"nested_total_length={nested}"
            )

    add_joints = observed["add_joints"]
    print("\nadd_joints() boundary:")
    print(f"  found: {add_joints['found']}")
    print(f"  owner: {add_joints['owner']}")
    print(f"  signature: {add_joints['signature']}")
    print(
        "  source: "
        f"{add_joints['source_file']}:{add_joints['source_start_line']}"
    )
    for name, value in add_joints["source_facts"].items():
        if name != "parse_error":
            print(f"  {name}: {value}")

    print("\nChecks:")
    for name, check in report["checks"].items():
        status = "PASS" if check["pass"] else "FAIL"
        print(
            f"  {status} {name}: "
            f"observed={check['observed']} expected={check['expected']}"
        )

    overall_status = "PASS" if report["overall_pass"] else "FAIL"
    print(f"\nOverall: {overall_status}")
    print(report["scientific_scope"])

    if args.output is not None:
        write_json_report(report, args.output)
        print(f"\nWrote JSON report: {args.output}")

    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
