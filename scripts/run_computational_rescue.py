#!/usr/bin/env python
"""Run Milestone E5 preregistered computational rescue validation."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.anatomy.audit import write_json_report  # noqa: E402
from drosophila_pd.experiments.computational_rescue import (  # noqa: E402
    build_computational_rescue_unavailable_report,
    load_computational_rescue_config,
    run_computational_rescue_validation,
)
from drosophila_pd.experiments.healthy_baseline import (  # noqa: E402
    load_healthy_baseline_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Milestone E5 preregistered computational rescue."
    )
    parser.add_argument(
        "--baseline-config",
        type=Path,
        default=REPO_ROOT / "configs" / "experiments" / "healthy_baseline.yaml",
        help="Path to the canonical baseline YAML configuration.",
    )
    parser.add_argument(
        "--validation-config",
        type=Path,
        required=True,
        help="Path to the E5 validation YAML configuration.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the E5 JSON report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    baseline_config = load_healthy_baseline_config(args.baseline_config)
    rescue_config = load_computational_rescue_config(args.validation_config)

    print("Milestone E5 preregistered computational rescue")
    print(f"Baseline config: {args.baseline_config}")
    print(f"Validation config: {args.validation_config}")
    print(f"Seeds: {list(rescue_config.seeds)}")
    print(f"Duration: {rescue_config.duration_s} s")
    print("Conditions:")
    for condition in rescue_config.conditions:
        print(
            f"  {condition.condition_id}: "
            f"motor={condition.motor_scale} coupling={condition.coupling_scale}"
        )

    try:
        report = run_computational_rescue_validation(
            baseline_config=baseline_config,
            rescue_config=rescue_config,
            repo_root=REPO_ROOT,
        )
    except Exception as exc:
        report = build_computational_rescue_unavailable_report(
            exc,
            baseline_config=baseline_config,
            rescue_config=rescue_config,
            repo_root=REPO_ROOT,
        )
        print("\nLOCAL EXECUTION = NOT VERIFIED")
        print(f"{type(exc).__name__}: {exc}")
        if args.output is not None:
            write_json_report(report, args.output)
            print(f"\nWrote JSON report: {args.output}")
        return 2

    print("\nSeed runs:")
    for seed_run in report["seed_runs"]:
        status = "PASS" if seed_run.get("overall_pass") else "FAIL"
        print(f"  {status} seed={seed_run['seed']} status={seed_run['status']}")

    print("\nCondition assessments:")
    for condition_id, assessment in report["condition_assessments"].items():
        classification = assessment.get("classification") or "REFERENCE"
        print(f"  {condition_id}: {classification}")

    print("\nE5 checks:")
    for name, check in report["checks"].items():
        status = "PASS" if check["pass"] else "FAIL"
        print(
            f"  {status} {name}: "
            f"observed={check['observed']} expected={check['expected']}"
        )

    overall_status = "PASS" if report["overall_pass"] else "FAIL"
    print(f"\nOverall report checks: {overall_status}")
    print(report["scientific_scope"])

    if args.output is not None:
        write_json_report(report, args.output)
        print(f"\nWrote JSON report: {args.output}")

    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
