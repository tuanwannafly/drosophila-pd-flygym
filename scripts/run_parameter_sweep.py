#!/usr/bin/env python
"""Run Milestone E0/E1 parameter-response sweeps."""

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
from drosophila_pd.experiments.parameter_sweep import (  # noqa: E402
    build_parameter_sweep_unavailable_report,
    load_parameter_sweep_config,
    run_parameter_sweep,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run Milestone E0/E1 generic parameter-response sweep."
    )
    parser.add_argument(
        "--baseline-config",
        type=Path,
        default=REPO_ROOT / "configs" / "experiments" / "healthy_baseline.yaml",
        help="Path to the unperturbed baseline YAML configuration.",
    )
    parser.add_argument(
        "--sweep-config",
        type=Path,
        required=True,
        help="Path to a parameter-sweep YAML configuration.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the combined sweep JSON report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    baseline_config = load_healthy_baseline_config(args.baseline_config)
    sweep_config = load_parameter_sweep_config(args.sweep_config)

    print("Milestone E0/E1 parameter-response sweep")
    print(f"Baseline config: {args.baseline_config}")
    print(f"Sweep config: {args.sweep_config}")
    print(f"Conditions: {len(sweep_config.conditions())}")

    try:
        report = run_parameter_sweep(
            baseline_config=baseline_config,
            sweep_config=sweep_config,
            repo_root=REPO_ROOT,
        )
    except Exception as exc:
        report = build_parameter_sweep_unavailable_report(
            exc,
            baseline_config=baseline_config,
            sweep_config=sweep_config,
            repo_root=REPO_ROOT,
        )
        print("\nLOCAL EXECUTION = NOT VERIFIED")
        print(f"{type(exc).__name__}: {exc}")
        if args.output is not None:
            write_json_report(report, args.output)
            print(f"\nWrote JSON report: {args.output}")
        return 2

    print("\nConditions:")
    for condition in report["conditions"]:
        status = "PASS" if condition.get("overall_pass") else "FAIL"
        print(
            "  "
            f"{status} {condition['condition_id']}: "
            f"{condition['parameter_name']}={condition['parameter_value']}"
        )

    print("\nSweep checks:")
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
