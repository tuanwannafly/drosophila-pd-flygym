#!/usr/bin/env python
"""Run Milestone 8B joint materialization and validation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.anatomy.materialization import (  # noqa: E402
    build_milestone_8b_materialization_report,
    build_milestone_8b_unavailable_report,
    instantiate_neuromechfly,
    runtime_environment,
    write_json_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Milestone 8B joint materialization and validation."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Optional path for a small JSON report, for example "
            "results/baseline/milestone_8b_materialization.json."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print("Milestone 8B joint materialization and post-materialization validation")
    print("Environment:")
    for key, value in runtime_environment().items():
        print(f"  {key}: {value}")

    try:
        fly = instantiate_neuromechfly()
        report = build_milestone_8b_materialization_report(fly, repo_root=REPO_ROOT)
    except Exception as exc:
        report = build_milestone_8b_unavailable_report(exc, repo_root=REPO_ROOT)
        print("\nLOCAL EXECUTION = NOT VERIFIED")
        print(f"{type(exc).__name__}: {exc}")
        if args.output is not None:
            write_json_report(report, args.output)
            print(f"\nWrote JSON report: {args.output}")
        return 2

    observed = report["observed"]
    print("\nPre-state:")
    print(f"  fly.skeleton is None: {observed['pre']['skeleton_after_is_none']}")
    print(
        "  JointDOF -> MJCF joint mapping: "
        f"{observed['pre']['jointdof_to_mjcfjoint_length']}"
    )
    print(
        "  JointDOF -> neutral angle mapping: "
        f"{observed['pre']['jointdof_to_neutralangle_length']}"
    )
    print(f"  MJCF root joints: {observed['pre']['mjcf_root_joint_count']}")

    print("\nMaterialization gate:")
    print(f"  gate: {observed['materialization']['gate_function']}")
    print(f"  operation: {observed['materialization']['operation']}")
    print(f"  created joints: {observed['materialization']['created_joint_count']}")

    print("\nPost-state:")
    print(f"  fly.skeleton is None: {observed['post']['skeleton_is_none']}")
    print(f"  JointDOFs: {observed['post']['jointdof_count']}")
    print(
        "  JointDOF -> MJCF joint mapping: "
        f"{observed['post']['jointdof_to_mjcfjoint_length']}"
    )
    print(
        "  JointDOF -> neutral angle mapping: "
        f"{observed['post']['jointdof_to_neutralangle_length']}"
    )
    print(f"  MJCF root joints: {observed['post']['mjcf_root_joint_count']}")
    print(
        "  actuator mapping total: "
        f"{observed['post']['actuator_mapping_total_length']}"
    )
    print(
        "  MJCF root actuators: "
        f"{observed['post']['mjcf_root_actuator_count']}"
    )

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
