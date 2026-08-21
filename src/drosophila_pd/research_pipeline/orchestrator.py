"""End-to-end computational study orchestration.

This module composes existing catalog, campaign, Digital Twin, measurement,
statistics, computational-PD, validation, publication, and provenance APIs.
It does not implement scientific algorithms and never starts FlyGym/MuJoCo.
"""

from __future__ import annotations

import json
import platform
import shutil
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from drosophila_pd.automation import DatasetCatalog, DatasetCatalogEntry, PublicationBuilder, ReproducibilityCenter, ResearchAutomationPlatform
from drosophila_pd.behavior_platform import CampaignFigureFactory, build_behavior_dashboard
from drosophila_pd.behavior_platform.campaign_provenance import file_sha256
from drosophila_pd.parkinson import ParkinsonMotorModel
from drosophila_pd.scientific_validation import generate_validation_report, validate_statistical_stability
from drosophila_pd.behavior_platform.measurement import measure_rollout_behavior
from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.digital_twin_platform import DigitalTwinPlatform
from drosophila_pd.research_campaign import Campaign, CampaignManager


PIPELINE_SCOPE = (
    "Unified computational study orchestration over supplied artifacts and existing "
    "V2 APIs only; no simulation, fabricated rollout, new scientific metric, or "
    "biological Parkinson's disease claim."
)

AnalysisStage = Callable[[Sequence[DatasetCatalogEntry], Path], Mapping[str, Any]]
StatisticsStage = Callable[[Mapping[str, Any], Path], Mapping[str, Any]]
ValidationStage = Callable[[Mapping[str, Any], Path], Mapping[str, Any]]


@dataclass(frozen=True)
class DatasetInput:
    """An existing dataset path registered without copying or changing it."""

    source: str | Path
    dataset_id: str
    name: str | None = None
    version: str = "1"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class StudyRequest:
    """Inputs and optional stage adapters for one computational study."""

    study_id: str
    name: str
    datasets: tuple[DatasetInput, ...] = ()
    campaign: Campaign | None = None
    digital_twin_platform: DigitalTwinPlatform | None = None
    rollouts: tuple[RolloutData, ...] = ()
    analysis_stage: AnalysisStage | None = None
    statistics_stage: StatisticsStage | None = None
    validation_stage: ValidationStage | None = None
    statistical_samples: Mapping[str, Sequence[float]] = field(default_factory=dict)
    observed_rollout: RolloutData | None = None
    reference_rollout: RolloutData | None = None
    computational_pd_model: ParkinsonMotorModel | None = None
    figure_records: tuple[Mapping[str, Any], ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StudyResult:
    """Paths and validation output from one study orchestration run."""

    study_root: Path
    manifest_path: Path
    package_path: Path
    validation: Mapping[str, Any]
    dashboard: Mapping[str, Any]


class StudyOrchestrator:
    """Connect existing research services into one deterministic workflow."""

    def __init__(self, repository_root: str | Path, output_root: str | Path | None = None) -> None:
        self.repository_root = Path(repository_root).resolve()
        self.output_root = Path(output_root or self.repository_root / "study_outputs").resolve()
        self.catalog = DatasetCatalog(self.output_root / "catalog")
        self.campaigns = CampaignManager(self.output_root / "campaigns")
        self.reproducibility = ReproducibilityCenter(self.repository_root)
        self.automation = ResearchAutomationPlatform(self.repository_root, self.output_root / "automation")

    def run(self, request: StudyRequest) -> StudyResult:
        """Execute the orchestration stages in their declared dependency order."""

        study_root = self.output_root / request.study_id
        directories = self._prepare(study_root)
        entries = self._register_datasets(request.datasets)
        campaign = self._ensure_campaign(request, directories["artifacts"])
        campaign_dashboard = self.campaigns.dashboard(campaign.campaign_id)

        twin_snapshot = request.digital_twin_platform.snapshot() if request.digital_twin_platform is not None else {
            "available": False,
            "reason": "No existing Digital Twin platform supplied.",
        }
        analysis = self._run_analysis(request, entries, directories["analysis"])
        statistics = self._run_statistics(request, analysis, directories["statistics"])
        computational_pd = self._run_computational_pd(request, directories["computational_pd"])
        validation = self._run_validation(request, analysis, directories["validation"])
        figures = self._run_figures(request, analysis, directories["figures"])
        reports = self._write_reports(
            request,
            campaign_dashboard,
            twin_snapshot,
            analysis,
            statistics,
            computational_pd,
            validation,
            figures,
            directories["reports"],
        )
        publication = self._build_publication(
            validation,
            reports,
            figures,
            directories["publication"],
        )
        dashboard = self._dashboard(request, entries, campaign_dashboard, validation, publication, analysis)
        manifest_path = self._write_study_manifest(
            request,
            study_root,
            entries,
            campaign,
            twin_snapshot,
            analysis,
            statistics,
            computational_pd,
            validation,
            figures,
            reports,
            publication,
            dashboard,
        )
        self.validate(request.study_id, study_root=study_root)
        package_path = self._build_package(study_root, manifest_path)
        final_validation = self.validate(request.study_id, study_root=study_root)
        return StudyResult(study_root, manifest_path, package_path, final_validation, dashboard)

    def validate(self, study_id: str, *, study_root: str | Path | None = None) -> dict[str, Any]:
        """Validate references, hashes, dependencies, and publication completeness."""

        root = Path(study_root or self.output_root / study_id)
        manifest_path = root / "study.json"
        if not manifest_path.is_file():
            return {"overall_pass": False, "reason": "study.json is missing", "scope": PIPELINE_SCOPE}
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        dataset_checks = self._validate_datasets(manifest.get("datasets", []))
        artifact_checks = self._validate_hashes(root, manifest.get("hashes", {}))
        references = manifest.get("references", {})
        reference_checks = {
            name: (root / path).is_file()
            for name, path in references.items()
            if isinstance(path, str)
        }
        publication = manifest.get("publication", {})
        publication_manifest = root / str(publication.get("manifest", "publication/manifest.json"))
        publication_checks = self._validate_publication(root, publication_manifest)
        dependency_checks = self._validate_campaign_dependencies(manifest.get("campaign", {}))
        checks = {
            "dependency_graph": dependency_checks,
            "datasets": dataset_checks,
            "references": reference_checks,
            "hash_consistency": artifact_checks,
            "publication_completeness": publication_checks,
            "study_manifest": manifest.get("study_id") == study_id,
        }
        result = {
            "study_id": study_id,
            "overall_pass": all(_all_pass(value) for value in checks.values()),
            "checks": checks,
            "scope": PIPELINE_SCOPE,
        }
        (root / "validation" / "pipeline_validation.json").write_text(
            json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return result

    def _register_datasets(self, inputs: Sequence[DatasetInput]) -> tuple[DatasetCatalogEntry, ...]:
        entries = []
        for item in inputs:
            entries.append(
                self.catalog.add(
                    item.source,
                    dataset_id=item.dataset_id,
                    name=item.name or item.dataset_id,
                    version=item.version,
                    **dict(item.metadata),
                )
            )
        return tuple(entries)

    def _ensure_campaign(self, request: StudyRequest, artifact_root: Path) -> Campaign:
        campaign = request.campaign or Campaign(name=request.name, metadata=dict(request.metadata))
        if campaign.campaign_id not in self.campaigns.campaigns:
            self.campaigns.create(campaign)
        self.campaigns.queue(campaign.campaign_id)
        self.campaigns.save(artifact_root / "campaign_manager.json")
        return campaign

    def _run_analysis(self, request: StudyRequest, entries: Sequence[DatasetCatalogEntry], output: Path) -> dict[str, Any]:
        if request.analysis_stage is not None:
            result = dict(request.analysis_stage(entries, output))
        elif request.rollouts:
            result = {
                "available": True,
                "rollout_count": len(request.rollouts),
                "measurements": [measure_rollout_behavior(rollout) for rollout in request.rollouts],
                "source": "existing measure_rollout_behavior API",
            }
        else:
            result = {"available": False, "reason": "No analysis stage or imported rollouts supplied."}
        return self._write_stage(output, "analysis.json", result)

    def _run_statistics(self, request: StudyRequest, analysis: Mapping[str, Any], output: Path) -> dict[str, Any]:
        if request.statistics_stage is not None:
            result = dict(request.statistics_stage(analysis, output))
        elif request.statistical_samples:
            result = validate_statistical_stability(request.statistical_samples)
        else:
            result = {"available": False, "reason": "No statistical sample arrays supplied."}
        return self._write_stage(output, "statistics.json", result)

    def _run_computational_pd(self, request: StudyRequest, output: Path) -> dict[str, Any]:
        if request.computational_pd_model is None or not request.rollouts:
            result = {"available": False, "reason": "No existing computational-PD model and rollout pair supplied."}
        else:
            result = {
                "available": True,
                "reports": [request.computational_pd_model.evaluate(rollout) for rollout in request.rollouts],
                "scope": "Existing computational PD API output only; no biological interpretation.",
            }
        return self._write_stage(output, "computational_pd.json", result)

    def _run_validation(self, request: StudyRequest, analysis: Mapping[str, Any], output: Path) -> dict[str, Any]:
        if request.validation_stage is not None:
            result = dict(request.validation_stage(analysis, output))
        elif request.observed_rollout is not None and request.reference_rollout is not None:
            result = generate_validation_report(
                request.observed_rollout,
                request.reference_rollout,
                output_dir=output,
                write_figures=True,
            )
        else:
            result = {"available": False, "reason": "No validation stage or observed/reference rollout pair supplied."}
        return self._write_stage(output, "validation_summary.json", result)

    def _run_figures(self, request: StudyRequest, analysis: Mapping[str, Any], output: Path) -> dict[str, Any]:
        records = request.figure_records or tuple(analysis.get("figure_records", ()))
        if not records:
            result = {"available": False, "reason": "No figure records supplied."}
        else:
            files = CampaignFigureFactory(output).generate_all(records, formats=("png", "svg"))
            result = {"available": True, "files": {key: path.relative_to(output).as_posix() for key, path in files.items()}}
        return self._write_stage(output, "figure_summary.json", result)

    def _write_reports(self, request, campaign, twins, analysis, statistics, computational_pd, validation, figures, output):
        payload = {
            "study_id": request.study_id,
            "name": request.name,
            "campaign": campaign,
            "digital_twins": twins,
            "analysis": _stage_reference(analysis, "analysis/analysis.json"),
            "statistics": _stage_reference(statistics, "statistics/statistics.json"),
            "computational_pd": _stage_reference(computational_pd, "computational_pd/computational_pd.json"),
            "validation": _stage_reference(validation, "validation/validation_summary.json"),
            "figures": _stage_reference(figures, "figures/figure_summary.json"),
            "scientific_scope": PIPELINE_SCOPE,
        }
        output.mkdir(parents=True, exist_ok=True)
        json_path = output / "study_report.json"
        json_path.write_text(json.dumps(_jsonable(payload), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path = output / "study_report.md"
        md_path.write_text(
            "# Study Report\n\n"
            f"- Study: `{request.name}`\n- Study ID: `{request.study_id}`\n"
            "- Scope: computational orchestration over supplied artifacts only.\n",
            encoding="utf-8",
        )
        return {"json": "reports/study_report.json", "markdown": "reports/study_report.md"}

    def _build_publication(self, validation, reports, figures, output):
        builder = PublicationBuilder(output)
        assets = []
        study_root = output.parent
        validation_dir = study_root / "validation"
        for path in sorted(validation_dir.glob("*.json")):
            assets.append(builder.register(path, "results"))
        report_dir = study_root / "reports"
        for path in sorted(report_dir.glob("*")):
            if path.is_file():
                assets.append(builder.register(path, "results"))
        figure_dir = study_root / "figures"
        for path in sorted(figure_dir.rglob("*")):
            if path.is_file():
                assets.append(builder.register(path, "figures"))
        manifest = builder.build(metadata={"source": "study orchestrator", "asset_count": len(assets)})
        return {"manifest": manifest.relative_to(study_root).as_posix(), "asset_count": len(assets)}

    def _write_study_manifest(self, request, root, entries, campaign, twins, analysis, statistics, computational_pd, validation, figures, reports, publication, dashboard):
        paths = [path for path in root.rglob("*") if path.is_file() and path.name not in {"study.json", "research_package.zip"}]
        provenance = self.reproducibility.collect(
            campaign_id=campaign.campaign_id,
            configuration={"study_id": request.study_id, "campaign": campaign.as_dict(), "metadata": dict(request.metadata)},
            dataset_paths=[entry.source for entry in entries],
            output_paths=paths,
        )
        hashes = {path.relative_to(root).as_posix(): file_sha256(path) for path in paths}
        checksum_path = root / "checksums" / "sha256.json"
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        checksum_path.write_text(json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest = {
            "study_manifest_version": 1,
            "study_id": request.study_id,
            "name": request.name,
            "datasets": [entry.as_dict() for entry in entries],
            "campaign": campaign.as_dict(),
            "digital_twins": twins,
            "analysis": _stage_reference(analysis, "analysis/analysis.json"),
            "statistics": _stage_reference(statistics, "statistics/statistics.json"),
            "computational_pd": _stage_reference(computational_pd, "computational_pd/computational_pd.json"),
            "validation": _stage_reference(validation, "validation/validation_summary.json"),
            "reports": reports,
            "figures": figures,
            "publication": publication,
            "references": {
                "analysis": "analysis/analysis.json",
                "statistics": "statistics/statistics.json",
                "computational_pd": "computational_pd/computational_pd.json",
                "validation": "validation/validation_summary.json",
                "report_json": reports["json"],
                "report_markdown": reports["markdown"],
                "figure_summary": "figures/figure_summary.json",
                "checksums": "checksums/sha256.json",
                "publication_manifest": publication["manifest"],
            },
            "hashes": hashes,
            "versions": {"python": platform.python_version(), "package": "drosophila-pd-flygym"},
            "provenance": provenance,
            "dashboard": dashboard,
            "scientific_scope": PIPELINE_SCOPE,
        }
        path = root / "study.json"
        path.write_text(json.dumps(_jsonable(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def _build_package(self, root: Path, manifest_path: Path) -> Path:
        target = root / "research_package.zip"
        readme = (
            "# Computational Research Package\n\n"
            "This package contains orchestration outputs and references to supplied "
            "computational artifacts. It does not contain new simulations or biological validation.\n"
        )
        with tempfile.TemporaryDirectory(prefix="study_package_") as temp:
            staging = Path(temp)
            for directory in ("reports", "validation", "figures", "tables", "publication", "artifacts", "checksums"):
                (staging / directory).mkdir()
            shutil.copy2(manifest_path, staging / "study.json")
            (staging / "README.md").write_text(readme, encoding="utf-8")
            for directory in ("reports", "validation", "figures", "tables", "publication", "artifacts", "checksums"):
                source = root / directory
                if source.exists():
                    for path in source.rglob("*"):
                        if path.is_file():
                            destination = staging / directory / path.relative_to(source)
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(path, destination)
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(staging.rglob("*")):
                    if path.is_dir():
                        archive.writestr(path.relative_to(staging).as_posix().rstrip("/") + "/", "")
                    else:
                        archive.write(path, path.relative_to(staging).as_posix())
        return target

    def _prepare(self, root: Path) -> dict[str, Path]:
        directories = {name: root / name for name in ("analysis", "statistics", "computational_pd", "validation", "reports", "figures", "tables", "publication", "artifacts", "checksums")}
        for path in directories.values():
            path.mkdir(parents=True, exist_ok=True)
        return directories

    def _dashboard(self, request, entries, campaign, validation, publication, analysis):
        records = request.figure_records or tuple(analysis.get("figure_records", ()))
        behavior_dashboard = (
            build_behavior_dashboard({str(index): record for index, record in enumerate(records)})
            if records
            else {"available": False, "reason": "No existing behavior reports supplied."}
        )
        return {
            "current_study": {"study_id": request.study_id, "name": request.name},
            "datasets": [entry.dataset_id for entry in entries],
            "campaigns": campaign,
            "validation": {"available": validation.get("available", validation.get("overall_pass", False)), "overall_pass": validation.get("overall_pass")},
            "publication": publication,
            "health": self.automation.health_check(),
            "behavior_dashboard": behavior_dashboard,
            "scientific_scope": PIPELINE_SCOPE,
        }

    def _validate_datasets(self, datasets):
        rows = []
        for entry in datasets:
            source = Path(entry["source"])
            exists = source.is_file() or source.is_dir()
            observed = file_sha256(source) if source.is_file() else None
            rows.append({"dataset_id": entry["dataset_id"], "exists": exists, "hash_match": observed == entry.get("sha256") if source.is_file() else exists})
        return {"overall_pass": all(row["exists"] and row["hash_match"] for row in rows), "rows": rows}

    def _validate_hashes(self, root, hashes):
        rows = []
        for relative, expected in hashes.items():
            path = root / relative
            rows.append({"path": relative, "exists": path.is_file(), "hash_match": path.is_file() and file_sha256(path) == expected})
        return {"overall_pass": all(row["exists"] and row["hash_match"] for row in rows), "rows": rows}

    def _validate_publication(self, root, manifest_path):
        if not manifest_path.is_file():
            return {"overall_pass": False, "reason": "publication manifest is missing"}
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows = []
        for asset in payload.get("assets", []):
            path = root / "publication" / asset["path"]
            rows.append({"path": asset["path"], "exists": path.is_file()})
        return {"overall_pass": all(row["exists"] for row in rows), "asset_count": len(rows), "rows": rows}

    def _validate_campaign_dependencies(self, campaign):
        experiments = {item["experiment_id"]: item for item in campaign.get("experiments", ())}
        rows = []
        for item in experiments.values():
            missing = [dependency for dependency in item.get("dependencies", ()) if dependency not in experiments]
            rows.append({"experiment_id": item["experiment_id"], "missing_dependencies": missing})
        return {"overall_pass": all(not row["missing_dependencies"] for row in rows), "rows": rows}

    def _write_stage(self, directory: Path, filename: str, result: Mapping[str, Any]) -> dict[str, Any]:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / filename
        path.write_text(json.dumps(_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return dict(result)


def run_study(request: StudyRequest, *, repository_root: str | Path, output_root: str | Path | None = None) -> StudyResult:
    """Convenience entry point for the unified workflow."""

    return StudyOrchestrator(repository_root, output_root).run(request)


def _stage_reference(result: Mapping[str, Any], path: str) -> dict[str, Any]:
    return {"available": result.get("available", True), "path": path}


def _all_pass(value: Any) -> bool:
    if isinstance(value, Mapping):
        if "overall_pass" in value and value["overall_pass"] is False:
            return False
        return all(_all_pass(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_all_pass(item) for item in value)
    return bool(value)


def _jsonable(value: Any) -> Any:
    if hasattr(value, "as_dict") and callable(value.as_dict):
        return _jsonable(value.as_dict())
    if hasattr(value, "tolist"):
        return value.tolist()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Path):
        return value.as_posix()
    return value


__all__ = ["PIPELINE_SCOPE", "DatasetInput", "StudyOrchestrator", "StudyRequest", "StudyResult", "run_study"]
