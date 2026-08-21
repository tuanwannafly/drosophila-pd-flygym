#!/usr/bin/env python
"""Run G7 measurement-enabled baseline/candidate evidence refresh."""

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
    load_candidate_robustness_config,
)
from drosophila_pd.experiments.healthy_baseline import (  # noqa: E402
    load_healthy_baseline_config,
)
from drosophila_pd.experiments.measurement_refresh import (  # noqa: E402
    DEFAULT_G7_OUTPUT_DIR,
    build_measurement_refresh_unavailable_report,
    load_measurement_extension_config,
    run_measurement_enabled_evidence_refresh,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run G7 measurement-enabled evidence refresh."
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
        default=(
            REPO_ROOT
            / "configs"
            / "experiments"
            / "validation"
            / "milestone_e3.yaml"
        ),
        help="Path to the frozen E3 validation YAML configuration.",
    )
    parser.add_argument(
        "--measurement-config",
        type=Path,
        default=REPO_ROOT / "configs" / "analysis" / "g5_measurement_extension.yaml",
        help="Path to the G5 measurement-extension YAML configuration.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPO_ROOT / DEFAULT_G7_OUTPUT_DIR,
        help="Directory for the new G7 evidence package.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    baseline_config = load_healthy_baseline_config(args.baseline_config)
    validation_config = load_candidate_robustness_config(args.validation_config)
    measurement_config = load_measurement_extension_config(args.measurement_config)

    print("G7 measurement-enabled evidence refresh")
    print(f"Baseline config: {args.baseline_config}")
    print(f"Validation config: {args.validation_config}")
    print(f"Measurement config: {args.measurement_config}")
    print(f"Output dir: {args.output_dir}")
    print(f"Seeds: {list(validation_config.seeds)}")
    print(f"Duration: {validation_config.duration_s} s")

    try:
        report = run_measurement_enabled_evidence_refresh(
            baseline_config=baseline_config,
            validation_config=validation_config,
            measurement_config=measurement_config,
            output_dir=args.output_dir,
            repo_root=REPO_ROOT,
        )
    except Exception as exc:
        report = build_measurement_refresh_unavailable_report(
            exc,
            baseline_config=baseline_config,
            validation_config=validation_config,
            measurement_config=measurement_config,
            output_dir=args.output_dir,
            repo_root=REPO_ROOT,
        )
        args.output_dir.mkdir(parents=True, exist_ok=True)
        report_path = args.output_dir / "measurement_enabled_evidence.json"
        write_json_report(report, report_path)
        print("\nLOCAL EXECUTION = NOT VERIFIED")
        print(f"{type(exc).__name__}: {exc}")
        print(f"Wrote unavailable report: {report_path}")
        return 2

    print("\nSeed pairs:")
    for pair in report["pairs"]:
        status = "PASS" if pair.get("overall_pass") else "FAIL"
        print(f"  {status} seed={pair['seed']} status={pair['status']}")

    print("\nG7 checks:")
    for name, check in report["checks"].items():
        status = "PASS" if check["pass"] else "FAIL"
        print(
            f"  {status} {name}: "
            f"observed={check['observed']} expected={check['expected']}"
        )

    print("\nArtifact counts:")
    for name, count in sorted(report["artifact_inventory"]["artifact_counts"].items()):
        print(f"  {name}: {count}")

    overall = "PASS" if report["overall_pass"] else "FAIL"
    print(f"\nOverall: {overall}")
    print(report["scientific_scope"])
    print(f"Wrote report: {args.output_dir / 'measurement_enabled_evidence.json'}")
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
