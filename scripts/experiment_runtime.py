"""CLI for dataset-bound experiment runtime orchestration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.experiment_runtime import ExperimentContext, ExperimentRuntime  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a scientific experiment over a discovered dataset.")
    parser.add_argument("command", choices=("prepare", "bind", "run", "status", "summary", "archive"))
    parser.add_argument("--root", type=Path, default=None)
    parser.add_argument("--experiment", default="experimental_campaign_01_healthy_baseline")
    parser.add_argument("--output", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = (args.root or ROOT).resolve()
    runtime = ExperimentRuntime(
        ExperimentContext(root, experiment_id=args.experiment, output_root=args.output)
    )
    if args.command == "prepare":
        payload = runtime.prepare()
    elif args.command == "bind":
        payload = runtime.bind()
    elif args.command == "run":
        payload = runtime.run()
    elif args.command == "status":
        payload = runtime.status()
    elif args.command == "summary":
        payload = runtime.summary()
    else:
        payload = runtime.archive()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
