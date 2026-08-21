"""Discover and execute a prepared campaign without running simulation code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.research_execution import ExecutionContext, ExecutionRuntime, ResearchAutomation  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dataset-gated research campaign execution.")
    parser.add_argument("--root", type=Path, default=None, help="Repository root (defaults to this checkout).")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("discover", "prepare", "execute", "batch", "progress", "status", "report", "bundle"):
        command = subparsers.add_parser(name)
        command.add_argument("--root", type=Path, default=None, help=argparse.SUPPRESS)
        command.add_argument("--campaign", default="experimental_campaign_01_healthy_baseline")
        command.add_argument("--output", type=Path, default=None)
        if name == "execute":
            command.add_argument("--limit", type=int, default=None, help="Run only the first N discovered rollouts.")
            command.add_argument("--no-resume", action="store_true", help="Reprocess completed rollout outputs.")
            command.add_argument("--no-retry-failed", action="store_true", help="Do not retry a previously failed rollout.")
        if name == "batch":
            command.add_argument("--limit", type=int, default=None, help="Run only the first N campaign jobs.")
            command.add_argument("--no-resume", action="store_true")
            command.add_argument("--no-retry-failed", action="store_true")
        if name in {"batch", "progress"}:
            command.add_argument("--progress-root", type=Path, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repository_root = (args.root or ROOT).resolve()
    context = ExecutionContext(
        repository_root,
        campaign_id=args.campaign,
        output_root=args.output,
    )
    runtime = ExecutionRuntime(context)
    if args.command == "discover":
        payload = runtime.discover().as_dict()
    elif args.command == "prepare":
        payload = runtime.prepare().as_dict()
    elif args.command == "execute":
        payload = runtime.execute(
            limit=args.limit,
            resume=not args.no_resume,
            retry_failed=not args.no_retry_failed,
        ).as_dict()
    elif args.command == "batch":
        payload = ResearchAutomation(context, progress_root=args.progress_root).execute(
            limit=args.limit,
            resume=not args.no_resume,
            retry_failed=not args.no_retry_failed,
        )
    elif args.command == "progress":
        payload = ResearchAutomation(context, progress_root=args.progress_root).progress()
    elif args.command == "status":
        payload = runtime.status()
    elif args.command == "report":
        payload = runtime.report()
    else:
        payload = runtime.bundle()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
