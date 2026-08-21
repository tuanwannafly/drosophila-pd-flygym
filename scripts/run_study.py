"""Run the unified orchestration workflow over supplied artifact paths."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from drosophila_pd.research_pipeline import DatasetInput, StudyOrchestrator, StudyRequest  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orchestrate one computational study without running simulation.")
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--dataset", action="append", default=[], metavar="DATASET_ID=PATH")
    parser.add_argument("--output-root", type=Path, default=Path("study_outputs"))
    args = parser.parse_args(argv)
    datasets = tuple(_dataset_input(value) for value in args.dataset)
    result = StudyOrchestrator(ROOT, args.output_root).run(
        StudyRequest(study_id=args.study_id, name=args.name, datasets=datasets)
    )
    print(json.dumps({"overall_pass": result.validation["overall_pass"], "study": result.manifest_path.as_posix(), "package": result.package_path.as_posix()}, indent=2, sort_keys=True))
    return 0 if result.validation["overall_pass"] else 1


def _dataset_input(value: str) -> DatasetInput:
    if "=" not in value:
        raise SystemExit("--dataset must use DATASET_ID=PATH")
    dataset_id, source = value.split("=", 1)
    if not dataset_id or not source:
        raise SystemExit("--dataset must use DATASET_ID=PATH")
    return DatasetInput(source=source, dataset_id=dataset_id)


if __name__ == "__main__":
    raise SystemExit(main())
