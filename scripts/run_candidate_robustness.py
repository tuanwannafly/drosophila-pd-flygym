#!/usr/bin/env python
"""Run Milestone E3 multi-seed candidate robustness validation."""

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
from drosophila_pd.experiments.candidate_robustness import (  # noqa: E402
    build_candidate_robustness_unavailable_report,
    load_candidate_robustness_config,
    run_candidate_robustness_validation,
)
from drosophila_pd.experiments.healthy_baseline import (  # noqa: E402
    load_healthy_baseline_config,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Milestone E3 frozen candidate robustness validation."
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
        help="Path to the E3 validation YAML configuration.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the E3 JSON report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    baseline_config = load_healthy_baseline_config(args.baseline_config)
    validation_config = load_candidate_robustness_config(args.validation_config)

    print("Milestone E3 candidate robustness validation")
    print(f"Baseline config: {args.baseline_config}")
    print(f"Validation config: {args.validation_config}")
    print(f"Seeds: {list(validation_config.seeds)}")
    print(f"Duration: {validation_config.duration_s} s")

    try:
        report = run_candidate_robustness_validation(
            baseline_config=baseline_config,
            validation_config=validation_config,
            repo_root=REPO_ROOT,
        )
    except Exception as exc:
        report = build_candidate_robustness_unavailable_report(
            exc,
            baseline_config=baseline_config,
            validation_config=validation_config,
            repo_root=REPO_ROOT,
        )
        print("\nLOCAL EXECUTION = NOT VERIFIED")
        print(f"{type(exc).__name__}: {exc}")
        if args.output is not None:
            write_json_report(report, args.output)
            print(f"\nWrote JSON report: {args.output}")
        return 2

    print("\nSeed pairs:")
    for pair in report["pairs"]:
        status = "PASS" if pair.get("overall_pass") else "FAIL"
        print(f"  {status} seed={pair['seed']} status={pair['status']}")

    print("\nE3 checks:")
    for name, check in report["checks"].items():
        status = "PASS" if check["pass"] else "FAIL"
        print(
            f"  {status} {name}: "
            f"observed={check['observed']} expected={check['expected']}"
        )

    assessment = report["robustness_assessment"]["classification"]
    overall_status = "PASS" if report["overall_pass"] else "FAIL"
    print(f"\nOverall: {overall_status}")
    print(f"Robustness assessment: {assessment}")
    print(report["scientific_scope"])

    if args.output is not None:
        write_json_report(report, args.output)
        print(f"\nWrote JSON report: {args.output}")

    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
