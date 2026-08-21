"""Analyze an already exported rollout without running a simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.parkinson.model import ParkinsonMotorConfig
from drosophila_pd.parkinson.report import generate_computational_pd_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Rollout JSON")
    parser.add_argument("--output", required=True, type=Path, help="Report directory")
    parser.add_argument("--reference", type=Path, help="JSON feature mapping or report")
    parser.add_argument("--config", type=Path, help="JSON/YAML computational config")
    args = parser.parse_args()

    rollout = RolloutData.from_mapping(json.loads(args.input.read_text(encoding="utf-8")))
    config = _load_config(args.config) if args.config else None
    reference = _load_reference(args.reference) if args.reference else None
    report = generate_computational_pd_report(
        rollout,
        output_dir=args.output,
        config=ParkinsonMotorConfig(**config) if isinstance(config, dict) else config,
        reference_features=reference,
    )
    print(json.dumps({"overall_pass": report["validation"]["report_checks"]["overall_pass"], "output": str(args.output)}))
    return 0


def _load_config(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(text) or {}
    return json.loads(text)


def _load_reference(path: Path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if "motor_features" in payload:
        return payload["motor_features"]["values"]
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
