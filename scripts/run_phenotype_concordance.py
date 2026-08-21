#!/usr/bin/env python
"""Build the Milestone E4 phenotype concordance report."""

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
from drosophila_pd.experiments.phenotype_concordance import (  # noqa: E402
    build_milestone_e4_concordance_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build Milestone E4 qualitative literature concordance from the "
            "curated evidence matrix and frozen E3 evidence."
        )
    )
    parser.add_argument(
        "--matrix",
        type=Path,
        default=REPO_ROOT / "docs" / "scientific" / "e4_evidence_matrix.yaml",
        help="Path to the curated E4 evidence matrix.",
    )
    parser.add_argument(
        "--e3-evidence",
        type=Path,
        default=(
            REPO_ROOT
            / "results"
            / "validation"
            / "milestone_e3_candidate_robustness.json"
        ),
        help="Path to the frozen E3 evidence JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the generated E4 JSON report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_milestone_e4_concordance_report(
        matrix_path=args.matrix,
        e3_evidence_path=args.e3_evidence,
        repo_root=REPO_ROOT,
    )

    print("Milestone E4 literature-grounded phenotype concordance")
    print(f"Matrix: {args.matrix}")
    print(f"E3 evidence: {args.e3_evidence}")
    print(
        "Overall scientific status: "
        f"{report['overall_scientific_status']['label']}"
    )

    print("\nConcordance assessments:")
    for assessment in report["concordance_assessments"]:
        print(
            f"  {assessment['classification']} "
            f"{assessment['literature_endpoint']} "
            f"({assessment['assessment_id']})"
        )

    print("\nE4 checks:")
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
