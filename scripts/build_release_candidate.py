"""Build the additive v1.0 release-candidate inventory."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.release_candidate import ReleaseCandidateBuilder, ReleaseCandidateConfig


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/release_candidate"))
    parser.add_argument("--version", default="v1.0.0-rc")
    args = parser.parse_args()
    output = args.output if args.output.is_absolute() else ROOT / args.output
    report = ReleaseCandidateBuilder(ROOT, ReleaseCandidateConfig(version=args.version, output_dir=str(output))).write(output)
    print(f"Generated {report['version']} release candidate in {output.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
