#!/usr/bin/env python
"""Run a paired Milestone D controlled perturbation experiment."""

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
from drosophila_pd.experiments.healthy_baseline import (  # noqa: E402
    load_healthy_baseline_config,
)
from drosophila_pd.experiments.perturbation_experiment import (  # noqa: E402
    build_perturbation_unavailable_report,
    run_paired_perturbation_experiment,
)
from drosophila_pd.perturbations import load_perturbation_config  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run baseline vs perturbed Milestone D paired experiment."
    )
    parser.add_argument(
        "--baseline-config",
        type=Path,
        default=REPO_ROOT / "configs" / "experiments" / "healthy_baseline.yaml",
        help="Path to the unperturbed baseline YAML configuration.",
    )
    parser.add_argument(
        "--perturbation-config",
        type=Path,
        required=True,
        help="Path to a controlled perturbation YAML configuration.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the paired JSON report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    baseline_config = load_healthy_baseline_config(args.baseline_config)
    perturbation = load_perturbation_config(args.perturbation_config)

    print("Milestone D controlled perturbation experiment")
    print(f"Baseline config: {args.baseline_config}")
    print(f"Perturbation config: {args.perturbation_config}")
    print(f"Perturbation: {perturbation.perturbation_type} / {perturbation.name}")

    try:
        report = run_paired_perturbation_experiment(
            baseline_config=baseline_config,
            perturbation=perturbation,
            repo_root=REPO_ROOT,
        )
    except Exception as exc:
        report = build_perturbation_unavailable_report(
            exc,
            baseline_config=baseline_config,
            perturbation=perturbation,
            repo_root=REPO_ROOT,
        )
        print("\nLOCAL EXECUTION = NOT VERIFIED")
        print(f"{type(exc).__name__}: {exc}")
        if args.output is not None:
            write_json_report(report, args.output)
            print(f"\nWrote JSON report: {args.output}")
        return 2

    print("\nChecks:")
    for name, check in report["checks"].items():
        status = "PASS" if check["pass"] else "FAIL"
        print(f"  {status} {name}: observed={check['observed']} expected={check['expected']}")

    comparison = report["comparison"]["scalars"]
    print("\nComparison:")
    for name in (
        "planar_displacement_mm",
        "mean_planar_speed_mm_s",
        "heading_yaw_change_rad",
    ):
        delta = comparison[name]["absolute_delta"]
        print(f"  {name} absolute_delta: {delta}")

    overall_status = "PASS" if report["overall_pass"] else "FAIL"
    print(f"\nOverall: {overall_status}")
    print(report["scientific_scope"])

    if args.output is not None:
        write_json_report(report, args.output)
        print(f"\nWrote JSON report: {args.output}")

    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
