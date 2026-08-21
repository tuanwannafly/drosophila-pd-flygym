"""CLI for the V9 Scientific Operating System kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from drosophila_pd.research_kernel import KernelContext, ResearchKernel


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate the orchestration-only research kernel.")
    parser.add_argument("command", choices=("boot", "status", "resources", "events", "shutdown"))
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--kernel-id", default="default")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--experiment", default="experimental_campaign_01_healthy_baseline")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    context = KernelContext(
        args.root,
        kernel_id=args.kernel_id,
        output_root=args.output,
        experiment_id=args.experiment,
    )
    kernel = ResearchKernel(context)
    if args.command == "boot":
        payload = kernel.boot()
    elif args.command == "status":
        payload = kernel.status()
    elif args.command == "resources":
        payload = kernel.resource_report()
    elif args.command == "events":
        payload = kernel.event_report()
    else:
        payload = kernel.shutdown()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
