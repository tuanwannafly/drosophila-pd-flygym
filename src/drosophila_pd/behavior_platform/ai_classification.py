"""Behavioral classifiers with reusable probability-style outputs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

import numpy as np


ClassifierPlugin = Callable[[Mapping[str, float]], tuple[str, float]]


@dataclass(frozen=True)
class ClassificationResult:
    sample_id: str
    label: str
    probabilities: Mapping[str, float]
    confidence: float
    classifier: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "label": self.label,
            "probabilities": dict(self.probabilities),
            "confidence": float(self.confidence),
            "classifier": self.classifier,
            "metadata": dict(self.metadata),
        }


def rule_based_classifier(
    sample_id: str,
    features: Mapping[str, float],
    *,
    rules: Mapping[str, Mapping[str, float]],
) -> ClassificationResult:
    """Classify by threshold rules of the form label -> feature thresholds."""

    scores = {}
    for label, thresholds in rules.items():
        passed = sum(float(features.get(name, 0.0)) >= float(value) for name, value in thresholds.items())
        scores[label] = passed / max(1, len(thresholds))
    probabilities = _normalize(scores)
    label = max(probabilities, key=probabilities.get)
    return ClassificationResult(sample_id, label, probabilities, probabilities[label], "rule_based")


def distance_based_classifier(
    sample_id: str,
    features: Mapping[str, float],
    *,
    prototypes: Mapping[str, Mapping[str, float]],
) -> ClassificationResult:
    """Classify by inverse distance to label prototypes."""

    names = sorted({name for proto in prototypes.values() for name in proto} | set(features))
    vector = np.asarray([features.get(name, 0.0) for name in names], dtype=float)
    scores = {}
    for label, proto in prototypes.items():
        target = np.asarray([proto.get(name, 0.0) for name in names], dtype=float)
        scores[label] = 1.0 / (1.0 + float(np.linalg.norm(vector - target)))
    probabilities = _normalize(scores)
    label = max(probabilities, key=probabilities.get)
    return ClassificationResult(sample_id, label, probabilities, probabilities[label], "distance_based")


def plugin_classifier(
    sample_id: str,
    features: Mapping[str, float],
    *,
    plugin: ClassifierPlugin,
    plugin_name: str = "custom_plugin",
) -> ClassificationResult:
    """Classify with a caller-supplied label plugin."""

    label, confidence = plugin(features)
    confidence = max(0.0, min(1.0, float(confidence)))
    return ClassificationResult(
        sample_id=sample_id,
        label=str(label),
        probabilities={str(label): confidence},
        confidence=confidence,
        classifier=plugin_name,
    )


def classify_feature_matrix(
    feature_matrix: Mapping[str, Any],
    *,
    classifier: str,
    rules: Mapping[str, Mapping[str, float]] | None = None,
    prototypes: Mapping[str, Mapping[str, float]] | None = None,
) -> dict[str, Any]:
    """Classify every row in a generated feature matrix."""

    names = feature_matrix["feature_names"]
    results = []
    for sample_id, row in zip(feature_matrix["sample_ids"], feature_matrix["matrix"]):
        features = {name: float(value) for name, value in zip(names, row)}
        if classifier == "rule_based":
            results.append(rule_based_classifier(sample_id, features, rules=rules or {}).as_dict())
        elif classifier == "distance_based":
            results.append(distance_based_classifier(sample_id, features, prototypes=prototypes or {}).as_dict())
        else:
            raise ValueError(f"unsupported classifier: {classifier}")
    return {
        "classification_version": 2,
        "classifier": classifier,
        "results": results,
        "label_counts": _label_counts(result["label"] for result in results),
    }


def _normalize(scores: Mapping[str, float]) -> dict[str, float]:
    if not scores:
        raise ValueError("classifier requires at least one label.")
    total = sum(max(0.0, float(value)) for value in scores.values())
    if total == 0:
        return {label: 1.0 / len(scores) for label in scores}
    return {label: max(0.0, float(value)) / total for label, value in scores.items()}


def _label_counts(labels: Sequence[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for label in labels:
        counts[label] = counts.get(label, 0) + 1
    return counts


__all__ = [
    "ClassificationResult",
    "ClassifierPlugin",
    "classify_feature_matrix",
    "distance_based_classifier",
    "plugin_classifier",
    "rule_based_classifier",
]
