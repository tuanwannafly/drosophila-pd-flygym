"""V2 research campaign utilities and Epic 20 lifecycle commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from drosophila_pd.behavior_platform import (  # noqa: E402
    CampaignArtifactManager,
    CampaignDatasetBuilder,
    CampaignFigureFactory,
    CampaignRunner,
    collect_campaign_provenance,
    create_campaign,
    generate_ai_behavior_report,
    generate_feature_matrix,
    generate_paper_assets,
    load_campaign_config,
    load_campaign_results,
    save_campaign,
    synthetic_behavior_dataset,
    verify_artifact_hashes,
    write_provenance_manifest,
)
from drosophila_pd.research_campaign import Campaign as ResearchCampaign  # noqa: E402
from drosophila_pd.research_campaign import CampaignManager  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Version 2 research campaign utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="create a deterministic plan or lifecycle campaign")
    create.add_argument("--config")
    create.add_argument("--output")
    create.add_argument("--name")
    create.add_argument("--description", default="")
    create.add_argument("--author", default="")
    create.add_argument("--state", type=Path)
    create.add_argument("--root", type=Path, default=Path("campaigns"))

    execute = subparsers.add_parser("execute", help="execute a campaign with the deterministic validation executor")
    execute.add_argument("--config", required=True)
    execute.add_argument("--output-dir", required=True)
    execute.add_argument("--max-experiments", type=int)

    resume = subparsers.add_parser("resume", help="resume a legacy checkpoint or lifecycle campaign")
    resume.add_argument("--config")
    resume.add_argument("--checkpoint")
    resume.add_argument("--output-dir")
    resume.add_argument("--state", type=Path)
    resume.add_argument("--campaign-id")

    dataset = subparsers.add_parser("dataset", help="build a dataset package from campaign result JSON files")
    dataset.add_argument("--input", nargs="+", required=True)
    dataset.add_argument("--dataset-id", default="campaign_dataset")
    dataset.add_argument("--output-dir", required=True)

    artifacts = subparsers.add_parser("artifacts", help="create deterministic artifact directories")
    artifacts.add_argument("--output-dir", required=True)

    figures = subparsers.add_parser("figures", help="generate campaign figure set from result JSON files")
    figures.add_argument("--input", nargs="*")
    figures.add_argument("--output-dir", required=True)
    figures.add_argument("--formats", nargs="+", default=["png"])

    report = subparsers.add_parser("report", help="generate a legacy report or lifecycle report")
    report.add_argument("--output-dir")
    report.add_argument("--state", type=Path)
    report.add_argument("--campaign-id")
    report.add_argument("--format", choices=("json", "md"), default="json")

    verify = subparsers.add_parser("verify", help="verify artifact hashes from a manifest")
    verify.add_argument("--manifest", required=True)

    for name in ("run", "pause", "cancel", "status", "history", "validate"):
        command = subparsers.add_parser(name, help=f"{name} a lifecycle campaign")
        command.add_argument("--state", type=Path, required=True)
        command.add_argument("--campaign-id", required=True)

    bundle = subparsers.add_parser("bundle", help="create a campaign publication pack")
    bundle.add_argument("--state", type=Path, required=True)
    bundle.add_argument("--campaign-id", required=True)
    bundle.add_argument("--output", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "create":
        return _create(args)
    if args.command == "execute":
        return _execute(args)
    if args.command == "resume":
        return _resume(args)
    if args.command == "dataset":
        return _dataset(args)
    if args.command == "artifacts":
        return _artifacts(args)
    if args.command == "figures":
        return _figures(args)
    if args.command == "report":
        return _report(args)
    if args.command == "verify":
        return _verify(args)
    return _lifecycle(args)


def _create(args: argparse.Namespace) -> int:
    if args.name:
        if args.state is None:
            raise SystemExit("lifecycle create requires --state")
        manager = CampaignManager(args.root)
        campaign = manager.create(ResearchCampaign(name=args.name, description=args.description, author=args.author))
        manager.save(args.state)
        _print({"overall_pass": True, "campaign_id": campaign.campaign_id, "state": args.state.as_posix()})
        return 0
    if not args.config or not args.output:
        raise SystemExit("legacy create requires --config and --output")
    path = save_campaign(create_campaign(load_campaign_config(args.config)), args.output)
    _print({"overall_pass": path.is_file(), "output": path.as_posix()})
    return 0


def _execute(args: argparse.Namespace) -> int:
    config = load_campaign_config(args.config)
    campaign = create_campaign(config)
    history, checkpoint = CampaignRunner().run(campaign, _validation_executor, output_dir=args.output_dir, max_experiments=args.max_experiments)
    provenance = collect_campaign_provenance(campaign_id=config.campaign_id, config=config.as_dict(), artifacts=[Path(args.output_dir) / "campaign_manifest.json", Path(args.output_dir) / "campaign_checkpoint.json"], seeds=config.seeds)
    provenance_path = write_provenance_manifest(provenance, Path(args.output_dir) / "provenance_manifest.json")
    _print({"overall_pass": not checkpoint.failed_ids, "completed": len(checkpoint.completed_ids), "failed": len(checkpoint.failed_ids), "history_events": len(history.events), "provenance": provenance_path.as_posix()})
    return 0 if not checkpoint.failed_ids else 1


def _resume(args: argparse.Namespace) -> int:
    if args.state:
        return _lifecycle(args)
    if not args.config or not args.checkpoint or not args.output_dir:
        raise SystemExit("legacy resume requires --config, --checkpoint, and --output-dir")
    config = load_campaign_config(args.config)
    checkpoint_data = json.loads(Path(args.checkpoint).read_text(encoding="utf-8"))
    from drosophila_pd.behavior_platform import CampaignCheckpoint

    history, checkpoint = CampaignRunner().run(create_campaign(config), _validation_executor, output_dir=args.output_dir, checkpoint=CampaignCheckpoint.from_dict(checkpoint_data))
    _print({"overall_pass": not checkpoint.failed_ids, "history_events": len(history.events)})
    return 0 if not checkpoint.failed_ids else 1


def _dataset(args: argparse.Namespace) -> int:
    files = CampaignDatasetBuilder(args.dataset_id).export_package(load_campaign_results(args.input), args.output_dir, formats=("json", "csv", "npz"))
    _print({"overall_pass": all(path.is_file() for path in files.values()), "files": _paths(files)})
    return 0


def _artifacts(args: argparse.Namespace) -> int:
    manager = CampaignArtifactManager(args.output_dir)
    layout = manager.prepare()
    manifest = manager.write_manifest()
    _print({"overall_pass": manifest.is_file(), "layout": _paths(layout), "manifest": manifest.as_posix()})
    return 0


def _figures(args: argparse.Namespace) -> int:
    reports = load_campaign_results(args.input) if args.input else tuple(_synthetic_reports())
    files = CampaignFigureFactory(args.output_dir).generate_all(reports, formats=args.formats)
    _print({"overall_pass": all(path.is_file() and path.stat().st_size > 0 for path in files.values()), "files": _paths(files)})
    return 0


def _report(args: argparse.Namespace) -> int:
    if args.state:
        manager = CampaignManager.load(args.state)
        path = manager.report(args.campaign_id, fmt=args.format)
        manager.save(args.state)
        _print({"overall_pass": path.is_file(), "path": path.as_posix()})
        return 0
    if not args.output_dir:
        raise SystemExit("legacy report requires --output-dir")
    output = Path(args.output_dir)
    dataset = synthetic_behavior_dataset(sample_count=4)
    features = generate_feature_matrix(dataset)
    report_files = generate_ai_behavior_report(dataset_summary=dataset.as_dict(), feature_summary=features, analysis_summary={"campaign_report": True}, benchmark_summary={"benchmark_report": {"case_count": 0}}, output_dir=output / "summary", formats=("markdown", "html", "pdf", "json", "csv"))
    paper_files = generate_paper_assets(figure_files={"summary": report_files["plot_png"]}, table_files={"summary": report_files["csv"]}, statistics_files={"summary": report_files["json"]}, output_dir=output)
    _print({"overall_pass": True, "report_files": _paths(report_files), "paper_files": _paths(paper_files)})
    return 0


def _verify(args: argparse.Namespace) -> int:
    report = verify_artifact_hashes(json.loads(Path(args.manifest).read_text(encoding="utf-8")))
    _print(report)
    return 0 if report["overall_pass"] else 1


def _lifecycle(args: argparse.Namespace) -> int:
    manager = CampaignManager.load(args.state)
    if args.command == "run":
        result = manager.run(args.campaign_id)
    elif args.command == "resume":
        result = manager.resume(args.campaign_id)
    elif args.command == "pause":
        result = manager.pause(args.campaign_id)
    elif args.command == "resume":
        result = manager.resume(args.campaign_id)
    elif args.command == "cancel":
        result = manager.cancel(args.campaign_id)
    elif args.command == "status":
        result = manager.dashboard(args.campaign_id)
    elif args.command == "history":
        result = manager.history(args.campaign_id).as_dict()
    elif args.command == "validate":
        result = manager.validate(args.campaign_id)
    elif args.command == "bundle":
        result = {"path": manager.bundle(args.campaign_id, args.output).as_posix(), "overall_pass": True}
    else:  # pragma: no cover - argparse restricts command names
        raise SystemExit(f"unsupported lifecycle command: {args.command}")
    manager.save(args.state)
    _print({"overall_pass": True, **result} if "overall_pass" not in result else result)
    return 0


def _validation_executor(plan: Any) -> Mapping[str, Any]:
    return {"experiment": plan.as_dict(), "condition": plan.role, "seed": plan.seed, "replicate": plan.replicate, "metrics": {"mean_speed": 1.0 + 0.01 * plan.seed, "yaw_rate_abs_mean": 0.05, "gait_score": 0.8, "exploration_index": 0.6, "comparison_score": 1.0, "benchmark_score": 1.0, "progression_stage_index": 0.0}, "metadata": {"validation_executor": True, "scientific_evidence": False}}


def _synthetic_reports() -> list[Mapping[str, Any]]:
    return [{"condition": sample.condition, "seed": index, "arrays": sample.arrays, "metrics": {"mean_speed": 1.0 + index, "exploration_index": 0.5 + index * 0.05}} for index, sample in enumerate(synthetic_behavior_dataset(sample_count=3).samples)]


def _paths(paths: Mapping[str, Path]) -> dict[str, str]:
    return {key: path.as_posix() for key, path in sorted(paths.items())}


def _print(payload: Mapping[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
