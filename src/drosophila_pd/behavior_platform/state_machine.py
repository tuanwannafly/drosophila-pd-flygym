"""Behavioral state machine for v2 timeline reconstruction."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from drosophila_pd.behavior_platform.data_model import BehaviorEpisode, BehaviorSequence


DEFAULT_STATES = ("Idle", "Walk", "Pause", "Turn", "Explore", "Recover")


@dataclass(frozen=True)
class BehaviorStateMachineConfig:
    speed_walk_threshold: float = 1.0
    speed_pause_threshold: float = 0.25
    yaw_turn_threshold_rad_s: float = 0.5
    radial_explore_threshold_mm: float | None = None
    recover_state_enabled: bool = True
    custom_state_labels: tuple[str, ...] = ()


def classify_behavior_states(
    *,
    speed_mm_s: Sequence[float],
    yaw_rate_rad_s: Sequence[float] | None = None,
    radial_distance_mm: Sequence[float] | None = None,
    recovery_mask: Sequence[bool] | None = None,
    custom_labels: Sequence[str | None] | None = None,
    config: BehaviorStateMachineConfig | Mapping[str, Any] | None = None,
) -> list[str]:
    """Classify per-sample behavior states from numeric time series."""

    settings = _coerce_config(config)
    speed = _finite_vector("speed_mm_s", speed_mm_s)
    yaw = np.zeros_like(speed) if yaw_rate_rad_s is None else _matching_vector("yaw_rate_rad_s", yaw_rate_rad_s, speed)
    radial = None if radial_distance_mm is None else _matching_vector("radial_distance_mm", radial_distance_mm, speed)
    recovery = np.zeros(speed.shape, dtype=bool) if recovery_mask is None else np.asarray(recovery_mask, dtype=bool)
    if recovery.shape != speed.shape:
        raise ValueError("recovery_mask sample count must match speed_mm_s.")
    custom = [None] * speed.size if custom_labels is None else list(custom_labels)
    if len(custom) != speed.size:
        raise ValueError("custom_labels sample count must match speed_mm_s.")

    labels = []
    for index, value in enumerate(speed):
        if custom[index]:
            labels.append(str(custom[index]))
        elif settings.recover_state_enabled and recovery[index]:
            labels.append("Recover")
        elif abs(yaw[index]) >= settings.yaw_turn_threshold_rad_s:
            labels.append("Turn")
        elif radial is not None and settings.radial_explore_threshold_mm is not None and radial[index] >= settings.radial_explore_threshold_mm:
            labels.append("Explore")
        elif value <= settings.speed_pause_threshold:
            labels.append("Pause")
        elif value >= settings.speed_walk_threshold:
            labels.append("Walk")
        else:
            labels.append("Idle")
    return labels


def analyze_state_sequence(
    labels: Sequence[str],
    *,
    timestep_s: float,
    sequence_id: str = "behavior_sequence",
) -> dict[str, Any]:
    """Compute transition, duration, episode, and timeline summaries."""

    if not labels:
        raise ValueError("labels must contain at least one state.")
    timestep = float(timestep_s)
    if not np.isfinite(timestep) or timestep <= 0:
        raise ValueError("timestep_s must be a positive finite number.")
    states = sorted(set(labels) | set(DEFAULT_STATES))
    transitions = _transition_counts(labels, states)
    probabilities = _transition_probabilities(transitions, states)
    episodes = _episodes(labels, timestep_s=timestep)
    sequence = BehaviorSequence(
        sequence_id=sequence_id,
        episodes=tuple(episodes),
        metadata={"sample_count": len(labels), "timestep_s": timestep},
    )
    return {
        "state_machine_version": 2,
        "scientific_scope": (
            "Behavioral states are computational labels inferred from supplied "
            "time series; they are not biological diagnoses."
        ),
        "states": states,
        "state_sequence": list(labels),
        "timeline": [
            {"sample_index": index, "time_s": index * timestep, "state": label}
            for index, label in enumerate(labels)
        ],
        "transition_graph": _transition_graph(transitions),
        "transition_counts": transitions,
        "transition_probabilities": probabilities,
        "transition_statistics": {
            "transition_count": int(sum(sum(row.values()) for row in transitions.values())),
            "unique_transition_count": int(sum(1 for row in transitions.values() for value in row.values() if value)),
        },
        "state_durations_s": {
            state: float(labels.count(state) * timestep) for state in states
        },
        "episodes": [episode.as_dict() for episode in episodes],
        "behavior_sequence": sequence.as_dict(),
    }


def reconstruct_state_timeline(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the timeline from a state-machine report."""

    return [dict(row) for row in report["timeline"]]


def _transition_counts(labels: Sequence[str], states: Sequence[str]) -> dict[str, dict[str, int]]:
    counts = {state: {target: 0 for target in states} for state in states}
    for before, after in zip(labels[:-1], labels[1:]):
        counts[before][after] += 1
    return counts


def _transition_probabilities(
    counts: Mapping[str, Mapping[str, int]],
    states: Sequence[str],
) -> dict[str, dict[str, float]]:
    probabilities: dict[str, dict[str, float]] = {}
    for state in states:
        total = sum(counts[state].values())
        probabilities[state] = {
            target: (counts[state][target] / total if total else 0.0)
            for target in states
        }
    return probabilities


def _transition_graph(counts: Mapping[str, Mapping[str, int]]) -> list[dict[str, Any]]:
    return [
        {"from_state": source, "to_state": target, "count": count}
        for source, row in counts.items()
        for target, count in row.items()
        if count > 0
    ]


def _episodes(labels: Sequence[str], *, timestep_s: float) -> list[BehaviorEpisode]:
    episodes: list[BehaviorEpisode] = []
    start = 0
    for index in range(1, len(labels) + 1):
        if index == len(labels) or labels[index] != labels[start]:
            episodes.append(
                BehaviorEpisode(
                    episode_id=f"episode_{len(episodes):04d}",
                    behavior_type=labels[start],
                    start_time_s=start * timestep_s,
                    end_time_s=index * timestep_s,
                    metadata={"start_sample": start, "end_sample_exclusive": index},
                )
            )
            start = index
    return episodes


def _coerce_config(config: BehaviorStateMachineConfig | Mapping[str, Any] | None) -> BehaviorStateMachineConfig:
    if config is None:
        return BehaviorStateMachineConfig()
    if isinstance(config, BehaviorStateMachineConfig):
        return config
    return BehaviorStateMachineConfig(**dict(config))


def _finite_vector(name: str, values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float).ravel()
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError(f"{name} must contain finite samples.")
    return array


def _matching_vector(name: str, values: Sequence[float], reference: np.ndarray) -> np.ndarray:
    array = _finite_vector(name, values)
    if array.shape != reference.shape:
        raise ValueError(f"{name} sample count must match speed_mm_s.")
    return array


__all__ = [
    "DEFAULT_STATES",
    "BehaviorStateMachineConfig",
    "analyze_state_sequence",
    "classify_behavior_states",
    "reconstruct_state_timeline",
]
