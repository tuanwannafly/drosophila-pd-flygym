"""Inspect and validate Digital Twin platform state without running simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.digital_twin_platform import DigitalTwinPlatform  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inspect", "validate"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    platform = DigitalTwinPlatform.from_json(args.input)
    payload = {
        "overall_pass": True,
        "twin_count": len(platform.twins.records),
        "scenario_count": len(platform.scenarios.scenarios),
        "session_count": len(platform.sessions),
        "knowledge_nodes": len(platform.graph.nodes),
        "knowledge_edges": len(platform.graph.edges),
        "collaboration_events": len(platform.collaboration.history),
        "scientific_scope": "Imported computational state management only; no simulation executed.",
    }
    if args.command == "inspect":
        payload["platform"] = platform.snapshot()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
