"""Export imported FlyGym rollout artifacts for the Three.js viewer."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.viewer_export import export_viewer_pose  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="Dataset directory or dataset ID, for example Healthy_001")
    parser.add_argument("--output", required=True, type=Path, help="Output viewer_pose.json path")
    parser.add_argument(
        "--dataset-root",
        action="append",
        type=Path,
        default=None,
        help="Additional root to search; may be supplied more than once",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = export_viewer_pose(args.dataset, args.output, search_roots=args.dataset_root)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
