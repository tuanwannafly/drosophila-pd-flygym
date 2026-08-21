"""Validate two already-imported rollout files without running simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.scientific_validation.datasets import ReferenceDatasetManager
from drosophila_pd.scientific_validation.report import generate_validation_report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--observed", required=True, type=Path, help="Imported observed rollout JSON")
    parser.add_argument("--reference", type=Path, help="Imported reference rollout JSON")
    parser.add_argument("--manifest", type=Path, help="Reference dataset manifest JSON")
    parser.add_argument("--reference-dataset", help="Dataset id in --manifest")
    parser.add_argument("--reference-entry", help="Entry id in --reference-dataset")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    observed = _load_json_rollout(args.observed)
    manager = None
    if args.reference:
        reference = _load_json_rollout(args.reference)
    elif args.manifest and args.reference_dataset and args.reference_entry:
        manager = ReferenceDatasetManager.from_manifest(args.manifest)
        reference = manager.get(args.reference_dataset).load(base_dir=args.manifest.parent)[args.reference_entry]
    else:
        parser.error("provide --reference or --manifest with --reference-dataset and --reference-entry")
    report = generate_validation_report(
        observed,
        reference,
        output_dir=args.output,
        manager=manager,
        manager_base_dir=args.manifest.parent if args.manifest else None,
    )
    print(json.dumps({"overall_pass": report["overall_pass"], "output": str(args.output)}))
    return 0


def _load_json_rollout(path: Path) -> RolloutData:
    return RolloutData.from_mapping(json.loads(path.read_text(encoding="utf-8")))


if __name__ == "__main__":
    raise SystemExit(main())
