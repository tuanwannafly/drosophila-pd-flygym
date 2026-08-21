"""Feature extraction for v2 AI-assisted behavioral analysis."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

import numpy as np

from drosophila_pd.behavior_platform.ai_dataset import BehaviorDataset, BehaviorSample
from drosophila_pd.behavior_platform.state_machine import analyze_state_sequence


FEATURE_FAMILIES = (
    "trajectory",
    "speed",
    "acceleration",
    "jerk",
    "heading",
    "yaw",
    "turning",
    "gait",
    "contact",
    "freezing",
    "exploration",
    "occupancy",
    "curvature",
    "tortuosity",
    "behavior_episodes",
    "state_statistics",
)


def extract_behavior_features(sample: BehaviorSample) -> dict[str, float]:
    """Extract deterministic scalar features from one sample."""

    arrays = {name: np.asarray(value, dtype=float) for name, value in sample.arrays.items()}
    positions = _positions(arrays)
    timestep = float(sample.metadata.get("timestep_s", 1.0))
    if timestep <= 0:
        raise ValueError("sample metadata timestep_s must be positive.")
    xy = positions[:, :2]
    step = np.linalg.norm(np.diff(xy, axis=0), axis=1)
    speed = step / timestep if step.size else np.zeros(0, dtype=float)
    acceleration = np.diff(speed) / timestep if speed.size > 1 else np.zeros(0, dtype=float)
    jerk = np.diff(acceleration) / timestep if acceleration.size > 1 else np.zeros(0, dtype=float)
    heading = _heading(arrays, xy)
    yaw_rate = np.diff(np.unwrap(heading)) / timestep if heading.size > 1 else np.zeros(0, dtype=float)
    curvature = _curvature(step, heading)
    contact = _contact_matrix(arrays)
    states = sample.metadata.get("state_sequence", ())
    state_report = analyze_state_sequence(states, timestep_s=timestep) if states else None
    features = {
        "trajectory_path_length_mm": float(np.sum(step)),
        "trajectory_displacement_mm": float(np.linalg.norm(xy[-1] - xy[0])),
        "speed_mean_mm_s": _mean(speed),
        "speed_max_mm_s": _max(speed),
        "acceleration_abs_mean_mm_s2": _abs_mean(acceleration),
        "jerk_abs_mean_mm_s3": _abs_mean(jerk),
        "heading_range_rad": _range(heading),
        "yaw_abs_rate_mean_rad_s": _abs_mean(yaw_rate),
        "turning_cumulative_rad": float(np.sum(np.abs(np.diff(np.unwrap(heading))))) if heading.size > 1 else 0.0,
        "curvature_abs_mean_rad_per_mm": _abs_mean(curvature),
        "tortuosity": _tortuosity(step, xy),
        "freezing_fraction": float(np.mean(speed <= float(sample.metadata.get("freeze_speed_threshold", 0.25)))) if speed.size else 0.0,
        "exploration_extent_x_mm": _range(xy[:, 0]),
        "exploration_extent_y_mm": _range(xy[:, 1]),
        "occupancy_unique_bins": float(_unique_bins(xy, bins=int(sample.metadata.get("occupancy_bins", 6)))),
    }
    if contact.size:
        features.update(
            {
                "contact_duty_factor": float(np.mean(contact)),
                "contact_transition_count": float(np.sum(np.abs(np.diff(contact, axis=1)))),
            }
        )
    else:
        features.update({"contact_duty_factor": 0.0, "contact_transition_count": 0.0})
    gait = sample.metadata.get("gait_summary", {})
    features["gait_stability_index"] = float(gait.get("stability_index", 0.0) or 0.0)
    features["gait_entropy_bits"] = float(gait.get("gait_entropy_bits", 0.0) or 0.0)
    if state_report:
        features["behavior_episode_count"] = float(len(state_report["episodes"]))
        features["state_unique_count"] = float(len(set(states)))
        features["state_transition_count"] = float(state_report["transition_statistics"]["transition_count"])
    else:
        features["behavior_episode_count"] = 0.0
        features["state_unique_count"] = 0.0
        features["state_transition_count"] = 0.0
    return {key: float(value) for key, value in sorted(features.items())}


def generate_feature_matrix(
    dataset: BehaviorDataset,
    *,
    feature_names: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Generate a feature matrix for all samples in a dataset."""

    rows = [extract_behavior_features(sample) for sample in dataset.samples]
    names = tuple(feature_names or sorted({key for row in rows for key in row}))
    matrix = np.asarray([[row.get(name, 0.0) for name in names] for row in rows], dtype=float)
    return {
        "feature_matrix_version": 2,
        "dataset_id": dataset.dataset_id,
        "sample_ids": [sample.sample_id for sample in dataset.samples],
        "conditions": [sample.condition for sample in dataset.samples],
        "feature_names": list(names),
        "matrix": matrix.tolist(),
        "finite": bool(np.isfinite(matrix).all()),
    }


def _positions(arrays: Mapping[str, np.ndarray]) -> np.ndarray:
    if "thorax_positions" in arrays:
        positions = arrays["thorax_positions"]
    elif "positions" in arrays:
        positions = arrays["positions"]
    else:
        raise ValueError("sample arrays require thorax_positions or positions.")
    if positions.ndim != 2 or positions.shape[1] < 2:
        raise ValueError("positions must have shape (n_samples, >=2).")
    if positions.shape[1] == 2:
        positions = np.column_stack([positions, np.zeros(positions.shape[0])])
    return positions[:, :3]


def _heading(arrays: Mapping[str, np.ndarray], xy: np.ndarray) -> np.ndarray:
    if "heading" in arrays:
        return np.asarray(arrays["heading"], dtype=float).ravel()
    if "yaw" in arrays:
        return np.asarray(arrays["yaw"], dtype=float).ravel()
    deltas = np.diff(xy, axis=0)
    values = np.zeros(xy.shape[0], dtype=float)
    if deltas.size:
        values[1:] = np.unwrap(np.arctan2(deltas[:, 1], deltas[:, 0]))
    return values


def _curvature(step: np.ndarray, heading: np.ndarray) -> np.ndarray:
    if heading.size < 2:
        return np.zeros(0, dtype=float)
    yaw_delta = np.diff(np.unwrap(heading))
    result = np.zeros_like(yaw_delta)
    moving = step > 1e-12
    result[moving] = yaw_delta[moving] / step[moving]
    return result


def _contact_matrix(arrays: Mapping[str, np.ndarray]) -> np.ndarray:
    contact_keys = [key for key in arrays if key.startswith("contact") or key.startswith("adhesion")]
    if not contact_keys:
        return np.zeros((0, 0), dtype=float)
    return np.vstack([np.asarray(arrays[key], dtype=float).ravel() > 0.5 for key in sorted(contact_keys)]).astype(float)


def _unique_bins(xy: np.ndarray, *, bins: int) -> int:
    if xy.shape[0] == 0:
        return 0
    span = np.ptp(xy, axis=0)
    span[span == 0] = 1.0
    normalized = (xy - np.min(xy, axis=0)) / span
    indices = np.floor(np.clip(normalized, 0, np.nextafter(1, 0)) * bins).astype(int)
    return len({tuple(row) for row in indices})


def _tortuosity(step: np.ndarray, xy: np.ndarray) -> float:
    path = float(np.sum(step))
    displacement = float(np.linalg.norm(xy[-1] - xy[0]))
    return path / displacement if displacement > 1e-12 else 0.0


def _mean(values: np.ndarray) -> float:
    return float(np.mean(values)) if values.size else 0.0


def _max(values: np.ndarray) -> float:
    return float(np.max(values)) if values.size else 0.0


def _abs_mean(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values))) if values.size else 0.0


def _range(values: np.ndarray) -> float:
    return float(np.ptp(values)) if values.size else 0.0


__all__ = ["FEATURE_FAMILIES", "extract_behavior_features", "generate_feature_matrix"]
