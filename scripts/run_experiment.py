"""Run one injected real experiment pipeline.

The CLI intentionally requires explicit stage handlers. It never imports
FlyGym by itself and never fabricates a rollout when a handler is absent.
"""

from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any

from drosophila_pd.experiment import ExperimentJob, ExperimentRunner, STAGE_NAMES


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an explicitly injected FlyGym experiment pipeline.")
    parser.add_argument("--config", required=True, type=Path, help="JSON job configuration")
    parser.add_argument("--output", required=True, type=Path, help="dataset/experiment output root")
    parser.add_argument(
        "--handler",
        action="append",
        default=[],
        metavar="STAGE=MODULE:FUNCTION",
        help="stage handler; repeat once for each canonical stage",
    )
    parser.add_argument("--resume", action="store_true", help="reuse persisted job metadata when available")
    args = parser.parse_args()

    config = _load_config(args.config)
    job = _load_job(config, args.output, resume=args.resume)
    handlers = _load_handlers(args.handler)
    result = ExperimentRunner(handlers).run(job)
    print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    return 0 if result.status.value == "COMPLETED" else 1


def _load_config(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to load YAML experiment configs.") from exc
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("experiment config must be an object")
    return payload


def _load_job(config: dict[str, Any], output: Path, *, resume: bool) -> ExperimentJob:
    job_path = output / str(config.get("job_id", config.get("experiment_id", "experiment"))) / "job.json"
    if resume and job_path.is_file():
        existing = json.loads(job_path.read_text(encoding="utf-8"))
        existing["output_root"] = str(output)
        existing["config"] = dict(config.get("config", existing.get("config", {})))
        return ExperimentJob.from_dict(existing)
    return ExperimentJob(
        job_id=str(config.get("job_id", config.get("experiment_id", "experiment"))),
        config=dict(config.get("config", config)),
        output_root=output,
        max_retries=int(config.get("max_retries", 0)),
        metadata=dict(config.get("metadata", {})),
    )


def _load_handlers(specs: list[str]) -> dict[str, Any]:
    handlers: dict[str, Any] = {}
    for spec in specs:
        if "=" not in spec or ":" not in spec:
            raise ValueError(f"handler must use STAGE=MODULE:FUNCTION: {spec}")
        stage, target = spec.split("=", 1)
        if stage not in STAGE_NAMES:
            raise ValueError(f"unknown stage: {stage}")
        module_name, function_name = target.rsplit(":", 1)
        function = getattr(importlib.import_module(module_name), function_name)
        if not callable(function):
            raise TypeError(f"handler is not callable: {spec}")
        handlers[stage] = function
    return handlers


if __name__ == "__main__":
    raise SystemExit(main())
