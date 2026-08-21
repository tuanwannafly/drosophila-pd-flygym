#!/usr/bin/env python
"""Run the CPU-only Milestone E6 evidence synthesis."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.analysis.evidence_synthesis import (  # noqa: E402
    EvidenceValidationError,
    run_evidence_synthesis,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Synthesize frozen evidence without running FlyGym or MuJoCo."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=REPO_ROOT / "configs" / "analysis" / "milestone_e6.yaml",
        help="Path to the E6 analysis YAML configuration.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "analysis" / "milestone_e6_synthesis.json",
        help="Path for the machine-readable synthesis report.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = run_evidence_synthesis(
            config_path=args.config,
            output_path=args.output,
            repo_root=REPO_ROOT,
        )
    except EvidenceValidationError as exc:
        print(f"E6 validation failed: {exc}")
        return 2
    except Exception as exc:
        print(f"E6 synthesis failed: {type(exc).__name__}: {exc}")
        return 2

    print(f"E6 synthesis: {'PASS' if report['overall_pass'] else 'FAIL'}")
    print(f"Wrote report: {args.output}")
    print(f"Figures: {len(report['artifacts']['figures'])}")
    print(f"Tables: {len(report['artifacts']['tables'])}")
    print(report["scientific_scope"])
    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
