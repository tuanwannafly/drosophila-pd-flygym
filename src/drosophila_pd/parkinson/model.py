"""Computational motor phenotype model over imported rollout data only."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData
from drosophila_pd.behavior_platform.state_machine import (
    analyze_state_sequence,
    classify_behavior_states,
)
from drosophila_pd.behavior_platform.measurement import measure_rollout_behavior


COMPUTATIONAL_SCOPE = (
    "Computational phenotype analysis over supplied rollout outputs only; "
    "not medical diagnosis, biological validation, disease severity, dopamine "
    "equivalence, mechanistic equivalence, or treatment evidence."
)

MOTOR_FEATURE_NAMES = (
    "walking_velocity_mm_s",
    "stride_velocity_mm_s",
    "cadence_hz",
    "acceleration_mm_s2",
    "angular_velocity_rad_s",
    "angular_acceleration_rad_s2",
    "com_displacement_mm",
    "com_stability_mm",
    "heading_stability_rad",
    "turning_rate_rad_s",
    "trajectory_curvature_rad_per_mm",
    "path_entropy_bits",
    "body_oscillation_mm",
    "body_sway_mm",
    "joint_rom_rad",
    "joint_velocity_rad_s",
    "joint_acceleration_rad_s2",
    "left_right_symmetry",
    "wing_motion_rad",
    "head_motion_mm",
)


@dataclass(frozen=True)
class ParkinsonMotorConfig:
    """Analysis configuration, never a clinical threshold configuration."""

    behavior: Mapping[str, Any] = field(default_factory=dict)
    index_weights: Mapping[str, float] = field(default_factory=dict)
    index_directions: Mapping[str, str] = field(default_factory=dict)
    bootstrap_replicates: int = 0
    bootstrap_seed: int = 0


class ParkinsonMotorModel:
    """Extract motor features and computational behavior states."""

    def __init__(self, config: ParkinsonMotorConfig | Mapping[str, Any] | None = None) -> None:
        if config is None:
            self.config = ParkinsonMotorConfig()
        elif isinstance(config, ParkinsonMotorConfig):
            self.config = config
        else:
            self.config = ParkinsonMotorConfig(**dict(config))

    def evaluate(self, rollout: RolloutData) -> dict[str, Any]:
        measured = measure_rollout_behavior(rollout, config=dict(self.config.behavior))
        features, samples = extract_motor_features(rollout, measured)
        behavior = build_behavior_model(rollout, measured, config=dict(self.config.behavior))
        index = ComputationalPDIndex(
            weights=self.config.index_weights,
            directions=self.config.index_directions,
            bootstrap_replicates=self.config.bootstrap_replicates,
            bootstrap_seed=self.config.bootstrap_seed,
        )
        return {
            "computational_pd_version": 1,
            "scientific_scope": COMPUTATIONAL_SCOPE,
            "rollout": rollout.as_metadata(),
            "motor_features": {
                "values": features,
                "available": {name: value is not None for name, value in features.items()},
                "sample_values": samples,
            },
            "behavior_model": behavior,
            "motor_impairment_indices": compute_motor_impairment_indices(features),
            "computational_pd_index": {
                "available": False,
                "reason": "A computational reference feature set is required.",
                "configuration": index.as_dict(),
            },
        }

    def evaluate_against_reference(
        self,
        rollout: RolloutData,
        reference_features: Mapping[str, float],
    ) -> dict[str, Any]:
        report = self.evaluate(rollout)
        index = ComputationalPDIndex(
            weights=self.config.index_weights,
            directions=self.config.index_directions,
            bootstrap_replicates=self.config.bootstrap_replicates,
            bootstrap_seed=self.config.bootstrap_seed,
        )
        report["computational_pd_index"] = index.evaluate(
            report["motor_features"]["values"],
            reference_features,
            sample_values=report["motor_features"]["sample_values"],
        )
        return report


def extract_motor_features(
    rollout: RolloutData,
    measured: Mapping[str, Any] | None = None,
) -> tuple[dict[str, float | None], dict[str, list[float]]]:
    """Extract the requested feature catalogue without fabricating absent data."""

    measured = measured or measure_rollout_behavior(rollout)
    positions = rollout.positions_array()
    timestep = rollout.timestep()
    trajectory = measured["trajectory"]
    speeds = np.asarray(trajectory.get("step_speed_mm_s", []), dtype=float)
    yaw_rate = np.asarray(measured.get("yaw_rate_rad_s", []), dtype=float)
    headings = np.asarray(measured.get("heading_rad", []), dtype=float)
    acceleration = np.diff(speeds) / timestep if speeds.size > 1 else np.array([])
    angular_acceleration = np.diff(yaw_rate) / timestep if yaw_rate.size > 1 else np.array([])
    joint_arrays = rollout.joint_arrays()
    joint_series = [array.ravel() for array in joint_arrays.values()]
    joint_velocity = _mean_abs([np.diff(array) / timestep for array in joint_series if array.size > 1])
    joint_acceleration = _mean_abs([np.diff(np.diff(array)) / timestep**2 for array in joint_series if array.size > 2])
    joint_ranges = [float(np.ptp(array)) for array in joint_series if array.size]
    com = rollout.com_array()
    com_displacement = _path_displacement(com) if com is not None else None
    com_stability = float(np.std(com[:, 2])) if com is not None else None
    named_values = {str(key).lower(): value for key, value in joint_arrays.items()}
    wing_arrays = [array for name, array in named_values.items() if "wing" in name]
    head_arrays = [array for name, array in named_values.items() if "head" in name]
    features: dict[str, float | None] = {
        "walking_velocity_mm_s": _mean(speeds),
        "stride_velocity_mm_s": _stride_velocity(measured),
        "cadence_hz": _metadata_number(rollout, "cadence_hz"),
        "acceleration_mm_s2": _mean_abs([acceleration]),
        "angular_velocity_rad_s": _mean_abs([yaw_rate]),
        "angular_acceleration_rad_s2": _mean_abs([angular_acceleration]),
        "com_displacement_mm": com_displacement,
        "com_stability_mm": com_stability,
        "heading_stability_rad": float(np.std(headings)) if headings.size else None,
        "turning_rate_rad_s": _mean_abs([yaw_rate]),
        "trajectory_curvature_rad_per_mm": _mean_abs([np.asarray(measured["path_geometry"].get("curvature_rad_per_mm", []), dtype=float)]),
        "path_entropy_bits": _metadata_number(rollout, "path_entropy_bits"),
        "body_oscillation_mm": float(np.std(positions[:, 2])) if positions.size else None,
        "body_sway_mm": float(np.std(positions[:, 1])) if positions.size else None,
        "joint_rom_rad": _mean(joint_ranges),
        "joint_velocity_rad_s": joint_velocity,
        "joint_acceleration_rad_s2": joint_acceleration,
        "left_right_symmetry": _left_right_symmetry(joint_arrays, rollout.adhesion_arrays()),
        "wing_motion_rad": _mean_abs([np.diff(array) / timestep for array in wing_arrays if array.size > 1]),
        "head_motion_mm": _mean_abs([np.diff(array) / timestep for array in head_arrays if array.size > 1]),
    }
    samples = {
        "walking_velocity_mm_s": speeds.tolist(),
        "angular_velocity_rad_s": np.abs(yaw_rate).tolist(),
        "body_oscillation_mm": positions[:, 2].tolist(),
        "body_sway_mm": positions[:, 1].tolist(),
    }
    return {name: _finite_or_none(features.get(name)) for name in MOTOR_FEATURE_NAMES}, samples


def build_behavior_model(
    rollout: RolloutData,
    measured: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build computational labels and transition/bout summaries."""

    config = dict(config or {})
    trajectory = measured["trajectory"]
    speeds = np.asarray(trajectory.get("instantaneous_speed_mm_s", []), dtype=float)
    yaw = np.asarray(measured.get("yaw_rate_rad_s", []), dtype=float)
    if speeds.size == 0:
        return {"available": False, "reason": "No trajectory speed samples."}
    if yaw.size != speeds.size:
        yaw = np.pad(yaw, (0, max(0, speeds.size - yaw.size)))[: speeds.size]
    positions = rollout.positions_array()
    radial = np.linalg.norm(positions[:, :2] - np.mean(positions[:, :2], axis=0), axis=1)
    custom = rollout.metadata.get("behavior_labels")
    labels = classify_behavior_states(
        speed_mm_s=speeds,
        yaw_rate_rad_s=yaw,
        radial_distance_mm=radial,
        custom_labels=custom,
        config=config.get("behavior_state", config),
    )
    report = analyze_state_sequence(labels, timestep_s=rollout.timestep())
    canonical_labels = [_canonical_behavior_label(label) for label in labels]
    canonical_report = analyze_state_sequence(canonical_labels, timestep_s=rollout.timestep())
    return {
        "available": True,
        "states": labels,
        "summary": report,
        "canonical_states": ["Walking", "Turning", "Standing", "Grooming", "Exploration", "Unknown"],
        "canonical_state_sequence": canonical_labels,
        "canonical_summary": canonical_report,
        "bout_statistics": {
            "walking": measured.get("walking_summary", {}),
            "turning": measured.get("turning_summary", {}),
            "freezing": measured.get("freezing", {}),
        },
        "scientific_scope": "Computational labels inferred from supplied rollout time series only.",
    }


@dataclass(frozen=True)
class ComputationalPDIndex:
    """Configurable weighted computational index, not a clinical score."""

    weights: Mapping[str, float] = field(default_factory=dict)
    directions: Mapping[str, str] = field(default_factory=dict)
    bootstrap_replicates: int = 0
    bootstrap_seed: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "weights": dict(self.weights),
            "directions": dict(self.directions),
            "bootstrap_replicates": int(self.bootstrap_replicates),
            "bootstrap_seed": int(self.bootstrap_seed),
            "scope": COMPUTATIONAL_SCOPE,
        }

    def evaluate(
        self,
        features: Mapping[str, float | None],
        reference: Mapping[str, float | None],
        *,
        sample_values: Mapping[str, Sequence[float]] | None = None,
    ) -> dict[str, Any]:
        from .validation import feature_ablation

        core = self._evaluate_core(features, reference)
        components = core["components"]
        index_value = core["value"]
        return {
            "available": index_value is not None,
            "value": index_value,
            "components": components,
            "feature_importance": _importance(components, index_value),
            "confidence": _completeness(components),
            "uncertainty": self._uncertainty(features, reference, sample_values),
            "sensitivity_analysis": feature_ablation(self, features, reference),
            "explainability": {
                "description": "Weighted relative computational deviations from a supplied reference.",
                "limitations": [
                    "Weights and directions are computational configuration, not clinical calibration.",
                    "No disease threshold or biological severity mapping is applied.",
                ],
            },
            "scope": COMPUTATIONAL_SCOPE,
        }

    def _uncertainty(self, features, reference, sample_values):
        if not self.bootstrap_replicates or not sample_values:
            return {"available": False, "reason": "Bootstrap samples were not configured or supplied."}
        values = []
        rng = np.random.default_rng(self.bootstrap_seed)
        for _ in range(int(self.bootstrap_replicates)):
            sampled = dict(features)
            for name, series in sample_values.items():
                array = np.asarray(series, dtype=float)
                if array.size:
                    sampled[name] = float(np.mean(rng.choice(array, size=array.size, replace=True)))
            result = self._evaluate_core(sampled, reference)["value"]
            if result is not None and np.isfinite(result):
                values.append(float(result))
        if not values:
            return {"available": False, "reason": "No finite bootstrap index values."}
        return {"available": True, "replicates": len(values), "low": float(np.percentile(values, 2.5)), "high": float(np.percentile(values, 97.5)), "mean": float(np.mean(values))}

    def _evaluate_core(self, features, reference):
        """Compute weighted components without recursive uncertainty work."""

        components: dict[str, Any] = {}
        weighted_scores: list[float] = []
        total_weight = 0.0
        for name, weight_value in self.weights.items():
            weight = float(weight_value)
            observed = _finite_or_none(features.get(name))
            baseline = _finite_or_none(reference.get(name))
            direction = self.directions.get(name, "lower_is_impairment")
            score = _deficit(observed, baseline, direction)
            available = score is not None and np.isfinite(weight) and weight >= 0
            components[name] = {
                "observed": observed,
                "reference": baseline,
                "direction": direction,
                "weight": weight,
                "score": score,
                "available": bool(available),
            }
            if available:
                total_weight += weight
                weighted_scores.append(weight * float(score))
        value = sum(weighted_scores) / total_weight if total_weight > 0 else None
        return {"value": value, "components": components}


def compute_motor_impairment_indices(features: Mapping[str, float | None]) -> dict[str, Any]:
    """Return named computational components without clinical interpretation."""

    pairs = {
        "bradykinesia_index": ("walking_velocity_mm_s", "lower_is_impairment"),
        "tremor_index": ("body_oscillation_mm", "higher_is_impairment"),
        "postural_stability_index": ("com_stability_mm", "higher_is_impairment"),
        "motor_consistency_index": ("heading_stability_rad", "higher_is_impairment"),
        "movement_smoothness": ("joint_acceleration_rad_s2", "lower_is_impairment"),
        "coordination_index": ("left_right_symmetry", "lower_is_impairment"),
        "symmetry_index": ("left_right_symmetry", "lower_is_impairment"),
        "energy_efficiency": ("walking_velocity_mm_s", "higher_is_impairment"),
    }
    return {
        name: {
            "feature": feature,
            "direction": direction,
            "value": _finite_or_none(features.get(feature)),
            "available": _finite_or_none(features.get(feature)) is not None,
            "scope": "Computational component only; no clinical interpretation.",
        }
        for name, (feature, direction) in pairs.items()
    }


def _deficit(observed, reference, direction):
    if observed is None or reference is None or abs(reference) <= 1e-12:
        return None
    if direction == "higher_is_impairment":
        return max(0.0, (observed - reference) / abs(reference))
    if direction == "absolute_change":
        return abs(observed - reference) / abs(reference)
    return max(0.0, (reference - observed) / abs(reference))


def _canonical_behavior_label(label: str) -> str:
    return {
        "Walk": "Walking",
        "Turn": "Turning",
        "Pause": "Standing",
        "Explore": "Exploration",
        "Idle": "Unknown",
        "Recover": "Unknown",
        "Walking": "Walking",
        "Turning": "Turning",
        "Standing": "Standing",
        "Grooming": "Grooming",
        "Exploration": "Exploration",
        "Unknown": "Unknown",
    }.get(str(label), "Unknown")


def _importance(components, index_value):
    if index_value is None or index_value == 0:
        return {name: 0.0 for name in components}
    total = sum(item["weight"] * (item["score"] or 0.0) for item in components.values() if item["available"])
    return {name: (item["weight"] * (item["score"] or 0.0) / total if total else 0.0) for name, item in components.items()}


def _completeness(components):
    return sum(item["available"] for item in components.values()) / len(components) if components else 0.0


def _left_right_symmetry(joints, adhesion):
    pairs = []
    names = list(joints)
    for name in names:
        lower = name.lower()
        if "left" in lower or lower.startswith("l_"):
            counterpart = lower.replace("left", "right", 1).replace("l_", "r_", 1)
            match = next((other for other in names if other.lower() == counterpart), None)
            if match:
                pairs.append((_mean_abs([joints[name]]), _mean_abs([joints[match]])))
    if not pairs and adhesion:
        left = [array for name, array in adhesion.items() if name.lower().startswith(("l", "left"))]
        right = [array for name, array in adhesion.items() if name.lower().startswith(("r", "right"))]
        if left and right: pairs.append((_mean_abs(left), _mean_abs(right)))
    if not pairs: return None
    values = [1.0 - abs(left - right) / max(abs(left), abs(right), 1e-12) for left, right in pairs]
    return float(np.mean(values))


def _stride_velocity(measured):
    turning = measured.get("turning_summary", {})
    stride_length = measured.get("summary", {}).get("stride_length")
    stride_frequency = measured.get("summary", {}).get("stride_frequency")
    if stride_length is not None and stride_frequency is not None:
        return _finite_or_none(float(stride_length) * float(stride_frequency))
    return None


def _path_displacement(value):
    if value is None or len(value) < 1: return None
    return float(np.linalg.norm(value[-1, :2] - value[0, :2]))


def _metadata_number(rollout, key):
    value = rollout.metadata.get(key)
    return _finite_or_none(value)


def _mean(values):
    finite = [float(value) for value in values if np.isfinite(float(value))]
    return float(np.mean(finite)) if finite else None


def _mean_abs(arrays):
    values = [np.abs(np.asarray(array, dtype=float).ravel()) for array in arrays if np.asarray(array).size]
    return _finite_or_none(float(np.mean(np.concatenate(values)))) if values else None


def _finite_or_none(value):
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if np.isfinite(result) else None


__all__ = [
    "COMPUTATIONAL_SCOPE",
    "MOTOR_FEATURE_NAMES",
    "ComputationalPDIndex",
    "ParkinsonMotorConfig",
    "ParkinsonMotorModel",
    "build_behavior_model",
    "compute_motor_impairment_indices",
    "extract_motor_features",
]
