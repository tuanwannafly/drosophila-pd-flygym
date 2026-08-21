"""Research summaries over existing computational artifacts.

The assistant is deliberately model-free. It reads caller-supplied analysis,
statistics, validation and report artifacts, then produces traceable summaries,
warnings and documentation prompts. It does not run simulation or scientific
analysis and does not infer biological meaning.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


ASSISTANT_SCOPE = (
    "Metadata-only orchestration over supplied computational artifacts; no AI "
    "model, simulation, new scientific algorithm, or biological inference."
)

_METRIC_EXPLANATIONS = {
    "velocity": "Speed or velocity values already reported by the supplied analysis artifact.",
    "acceleration": "Change in a supplied velocity series over the recorded time steps.",
    "stride_length": "Stride-length value already computed by the supplied gait analysis.",
    "stride_frequency": "Stride-frequency value already computed by the supplied gait analysis.",
    "com": "Center-of-mass position or derived series supplied by the rollout analysis.",
    "turning": "Turning or yaw-derived values supplied by the locomotion analysis.",
    "freezing": "Pause or immobility values supplied by the behavioral assay output.",
}

_CHART_EXPLANATIONS = {
    "trajectory": "A visual representation of supplied position samples over time.",
    "speed": "A chart of the supplied speed or velocity time series.",
    "gait": "A chart of supplied contact, stride, or coordination outputs.",
    "validation": "A visual summary of supplied validation checks and errors.",
    "distribution": "A visual summary of supplied values; it does not add a statistical test.",
}


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


@dataclass(frozen=True)
class AssistantReport:
    """Serializable assistant output with explicit computational scope."""

    summary: Mapping[str, Any] = field(default_factory=dict)
    findings: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    publication_notes: tuple[str, ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    scientific_scope: str = ASSISTANT_SCOPE

    def as_dict(self) -> dict[str, Any]:
        return {
            "assistant_version": 1,
            "summary": _jsonable(self.summary),
            "findings": list(self.findings),
            "warnings": list(self.warnings),
            "recommendations": list(self.recommendations),
            "publication_notes": list(self.publication_notes),
            "provenance": _jsonable(self.provenance),
            "scientific_scope": self.scientific_scope,
        }


class ResearchAssistant:
    """Generate explanations and checks from existing artifacts only."""

    def __init__(
        self,
        artifact_root: str | Path | Mapping[str, Any] | None = None,
        *,
        artifacts: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if isinstance(artifact_root, Mapping) and artifacts is None:
            artifacts = artifact_root
            artifact_root = None
        self.artifact_root = Path(artifact_root).resolve() if artifact_root is not None else None
        self.artifacts = dict(artifacts or {})
        self.metadata = dict(metadata or {})

    def read_artifacts(self) -> dict[str, Any]:
        """Read explicitly supplied files or conventional artifact folders."""

        result = {key: _materialize_artifact(value) for key, value in self.artifacts.items()}
        if self.artifact_root is None:
            return {key: _jsonable(value) for key, value in result.items()}
        for category in ("dataset", "analysis", "statistics", "validation", "reports"):
            if category in result:
                continue
            directory = self.artifact_root / category
            if directory.is_file():
                result[category] = _read_json(directory)
            elif directory.is_dir():
                result[category] = _read_first_json(directory)
        return {key: _jsonable(value) for key, value in result.items()}

    def generate(self) -> AssistantReport:
        artifacts = self.read_artifacts()
        summary = self._summary(artifacts)
        findings = self._findings(artifacts)
        warnings = self._warnings(artifacts)
        recommendations = self._recommendations(artifacts, warnings)
        notes = (
            "Use the original manuscript and supplied report artifacts for publication wording.",
            "Assistant output is a computational documentation aid, not biological validation.",
        )
        return AssistantReport(
            summary=summary,
            findings=tuple(findings),
            warnings=tuple(warnings),
            recommendations=tuple(recommendations),
            publication_notes=notes,
            provenance={"generated_at": _timestamp(), "artifact_root": str(self.artifact_root) if self.artifact_root else None, **self.metadata},
        )

    def explain_metric(self, metric: str) -> str:
        key = str(metric).strip().casefold().replace(" ", "_")
        return _METRIC_EXPLANATIONS.get(key, "No registered explanation is available for this metric artifact.")

    def explain_chart(self, chart: str) -> str:
        key = str(chart).strip().casefold().replace(" ", "_")
        return _CHART_EXPLANATIONS.get(key, "No registered explanation is available for this chart.")

    def explain_validation(self, validation: Mapping[str, Any] | None = None) -> str:
        payload = dict(validation or self.read_artifacts().get("validation", {}) or {})
        if payload.get("overall_pass") is True:
            return "The supplied validation artifact reports pass for its declared computational checks."
        if payload.get("overall_pass") is False:
            return "The supplied validation artifact reports a failed computational check; inspect its details."
        return "No overall validation status is available in the supplied artifacts."

    def detect_anomalies(self, value: Any | None = None) -> list[str]:
        """Report only structural/non-finite anomalies found in supplied data."""

        payload = self.read_artifacts() if value is None else value
        anomalies: list[str] = []
        _collect_nonfinite(payload, "root", anomalies)
        if isinstance(payload, Mapping):
            validation = payload.get("validation")
            if isinstance(validation, Mapping) and validation.get("overall_pass") is False:
                anomalies.append("validation.overall_pass is false")
        return sorted(set(anomalies))

    def recommend_next_experiment(self, report: AssistantReport | None = None) -> list[str]:
        """Return workflow recommendations without choosing scientific parameters."""

        current = report or self.generate()
        if current.warnings:
            return ["Resolve the listed artifact and validation warnings before planning the next comparison."]
        return [
            "Use the existing campaign matrix to define the next computational comparison.",
            "Keep seeds, configurations, and validation criteria in the campaign provenance.",
        ]

    def write(self, output_dir: str | Path, report: AssistantReport | None = None) -> dict[str, Path]:
        result = report or self.generate()
        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        json_path = output / "assistant_report.json"
        markdown_path = output / "assistant_report.md"
        json_path.write_text(json.dumps(result.as_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        markdown_path.write_text(render_markdown(result), encoding="utf-8")
        return {"json": json_path, "markdown": markdown_path}

    def _summary(self, artifacts: Mapping[str, Any]) -> dict[str, Any]:
        availability = {category: _available(artifacts.get(category)) for category in ("dataset", "analysis", "statistics", "validation", "reports")}
        return {
            "artifact_availability": availability,
            "available_artifacts": sum(availability.values()),
            "total_artifact_categories": len(availability),
            "validation_status": _validation_status(artifacts.get("validation")),
            "anomaly_count": len(self.detect_anomalies(artifacts)),
        }

    def _findings(self, artifacts: Mapping[str, Any]) -> list[str]:
        findings = []
        for category in ("dataset", "analysis", "statistics", "validation", "reports"):
            if _available(artifacts.get(category)):
                findings.append(f"{category.capitalize()} artifact is available for review.")
        validation_status = _validation_status(artifacts.get("validation"))
        findings.append(f"Validation artifact status: {validation_status}.")
        return findings

    def _warnings(self, artifacts: Mapping[str, Any]) -> list[str]:
        warnings = [f"Missing {category} artifact." for category in ("dataset", "analysis", "statistics", "validation", "reports") if not _available(artifacts.get(category))]
        warnings.extend(self.detect_anomalies(artifacts))
        return sorted(set(warnings))

    def _recommendations(self, artifacts: Mapping[str, Any], warnings: list[str]) -> list[str]:
        if warnings:
            return ["Resolve missing or anomalous supplied artifacts before interpreting the report."]
        return self.recommend_next_experiment(AssistantReport(warnings=()))


def render_markdown(report: AssistantReport) -> str:
    payload = report.as_dict()
    lines = ["# Research Assistant Report", "", "## Summary", "", "```json", json.dumps(payload["summary"], indent=2, sort_keys=True), "```", "", "## Findings", ""]
    lines.extend(f"- {item}" for item in payload["findings"])
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in payload["warnings"] or ["None recorded."])
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in payload["recommendations"])
    lines.extend(["", "## Publication Notes", ""])
    lines.extend(f"- {item}" for item in payload["publication_notes"])
    lines.extend(["", "## Scientific Scope", "", report.scientific_scope, ""])
    return "\n".join(lines)


def _available(value: Any) -> bool:
    return value is not None and value != {} and value != []


def _validation_status(value: Any) -> str:
    if not isinstance(value, Mapping):
        return "UNAVAILABLE"
    if value.get("overall_pass") is True:
        return "PASS"
    if value.get("overall_pass") is False:
        return "FAIL"
    return "UNAVAILABLE"


def _read_first_json(directory: Path) -> dict[str, Any]:
    for path in sorted(directory.glob("*.json")):
        payload = _read_json(path)
        if payload:
            return payload
    return {}


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _materialize_artifact(value: Any) -> Any:
    """Load an explicitly supplied JSON path while preserving inline artifacts."""

    if isinstance(value, Path):
        return _read_json(value) if value.is_file() else {}
    if isinstance(value, str):
        path = Path(value)
        if path.is_file() and path.suffix.casefold() == ".json":
            return _read_json(path)
    return value


def _collect_nonfinite(value: Any, path: str, output: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            _collect_nonfinite(child, f"{path}.{key}", output)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _collect_nonfinite(child, f"{path}[{index}]", output)
    elif isinstance(value, float) and not math.isfinite(value):
        output.append(f"non-finite value at {path}")


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


__all__ = ["ASSISTANT_SCOPE", "AssistantReport", "ResearchAssistant", "render_markdown"]
