"""Gait, contact, and coordination analysis for v2 rollout arrays."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

import numpy as np

from drosophila_pd.behavior_platform.rollout import ArrayLike, RolloutData


CANONICAL_LEG_ORDER = ("LF", "LM", "LH", "RF", "RM", "RH")
LEFT_RIGHT_PAIRS = (("LF", "RF"), ("LM", "RM"), ("LH", "RH"))
TRIPOD_A = ("LF", "RM", "LH")
TRIPOD_B = ("RF", "LM", "RH")
SUPPORTED_GAIT_INPUTS = (
    "binary contact state",
    "adhesion output thresholded at 0.5",
    "optional foot positions",
    "optional joint trajectories",
)


@dataclass(frozen=True)
class GaitAnalysisConfig:
    """Thresholds and grouping choices for deterministic gait analysis."""

    contact_threshold: float = 0.5
    min_contact_duration_s: float = 0.0
    min_swing_duration_s: float = 0.0
    min_stride_duration_s: float = 0.0
    transition_smoothing_samples: int = 0
    phase_reference_legs: tuple[str, ...] = CANONICAL_LEG_ORDER


@dataclass(frozen=True)
class GaitInput:
    """Canonical gait-analysis input detached from simulation state."""

    condition_id: str
    timestep_s: float
    contact_states: Mapping[str, ArrayLike]
    sample_id: str | None = None
    foot_positions: Mapping[str, ArrayLike] | None = None
    joint_trajectories: Mapping[str, ArrayLike] | None = None
    adhesion_outputs: Mapping[str, ArrayLike] | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_rollout(
        cls,
        rollout: RolloutData,
        *,
        contact_source: str = "adhesion",
        foot_positions: Mapping[str, ArrayLike] | None = None,
    ) -> "GaitInput":
        """Build gait input from an existing rollout package.

        The default contact source is the rollout's adhesion outputs. The
        method is pure post-processing and does not inspect or mutate FlyGym.
        """

        if contact_source != "adhesion":
            raise ValueError("only contact_source='adhesion' is currently supported.")
        contacts = rollout.adhesion_arrays()
        if not contacts:
            raise ValueError("rollout has no adhesion_outputs to use as contacts.")
        return cls(
            condition_id=rollout.condition_id,
            sample_id=rollout.sample_id,
            timestep_s=rollout.timestep(),
            contact_states=contacts,
            foot_positions=foot_positions,
            joint_trajectories=rollout.joint_arrays(),
            adhesion_outputs=contacts,
            metadata=rollout.metadata,
        )

    def timestep(self) -> float:
        value = float(self.timestep_s)
        if not np.isfinite(value) or value <= 0:
            raise ValueError("timestep_s must be a positive finite number.")
        return value

    def contact_arrays(self, *, threshold: float = 0.5) -> dict[str, np.ndarray]:
        contacts: dict[str, np.ndarray] = {}
        for leg, values in self.contact_states.items():
            array = np.asarray(values, dtype=float).ravel()
            if array.size == 0 or not np.isfinite(array).all():
                raise ValueError(f"contact_states[{leg!r}] must contain finite samples.")
            contacts[str(leg)] = array > threshold
        _validate_equal_sample_counts(contacts, "contact_states")
        return contacts

    def foot_arrays(self) -> dict[str, np.ndarray]:
        return _matrix_mapping(self.foot_positions or {}, "foot_positions", width=3)

    def joint_arrays(self) -> dict[str, np.ndarray]:
        arrays: dict[str, np.ndarray] = {}
        for name, values in (self.joint_trajectories or {}).items():
            array = np.asarray(values, dtype=float)
            if array.ndim == 0 or array.shape[0] == 0 or not np.isfinite(array).all():
                raise ValueError(f"joint_trajectories[{name!r}] must contain finite samples.")
            arrays[str(name)] = array
        return arrays

    def sample_count(self) -> int:
        contacts = self.contact_arrays()
        samples = next(iter(contacts.values())).size
        for name, array in self.foot_arrays().items():
            if array.shape[0] != samples:
                raise ValueError(f"foot_positions[{name!r}] sample count mismatch.")
        for name, array in self.joint_arrays().items():
            if array.shape[0] != samples:
                raise ValueError(f"joint_trajectories[{name!r}] sample count mismatch.")
        return int(samples)

    def time_s(self) -> np.ndarray:
        return np.arange(self.sample_count(), dtype=float) * self.timestep()

    def as_metadata(self) -> dict[str, Any]:
        return {
            "condition_id": self.condition_id,
            "sample_id": self.sample_id,
            "sample_count": self.sample_count(),
            "timestep_s": self.timestep(),
            "metadata": dict(self.metadata),
        }


def analyze_gait(
    gait_input: GaitInput,
    *,
    config: GaitAnalysisConfig | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute complete gait, contact, and coordination metrics."""

    settings = _coerce_config(config)
    contacts = gait_input.contact_arrays(threshold=settings.contact_threshold)
    sample_count = gait_input.sample_count()
    timestep = gait_input.timestep()
    leg_order = _ordered_legs(contacts)
    time_s = np.arange(sample_count, dtype=float) * timestep
    foot_positions = gait_input.foot_arrays()
    joints = gait_input.joint_arrays()
    contact_matrix = np.vstack([contacts[leg].astype(int) for leg in leg_order])

    stance_bouts = {
        leg: _segments_to_bouts(
            contacts[leg],
            timestep_s=timestep,
            label="stance",
            min_duration_s=settings.min_contact_duration_s,
        )
        for leg in leg_order
    }
    swing_bouts = {
        leg: _segments_to_bouts(
            ~contacts[leg],
            timestep_s=timestep,
            label="swing",
            min_duration_s=settings.min_swing_duration_s,
        )
        for leg in leg_order
    }
    stride_events = {
        leg: _stride_events(
            leg=leg,
            stance_bouts=stance_bouts[leg],
            foot_positions=foot_positions.get(leg),
            timestep_s=timestep,
            min_stride_duration_s=settings.min_stride_duration_s,
        )
        for leg in leg_order
    }
    duty_factor = {
        leg: _json_float(np.count_nonzero(contacts[leg]) / sample_count)
        for leg in leg_order
    }
    stride_duration = {
        leg: _summary([event["duration_s"] for event in events])
        for leg, events in stride_events.items()
    }
    stride_length = {
        leg: _summary([event["stride_length_mm"] for event in events])
        for leg, events in stride_events.items()
    }
    cadence = {
        leg: _json_float(len(stride_events[leg]) / _duration_s(sample_count, timestep))
        for leg in leg_order
    }
    phase = _inter_leg_phase(stride_events, leg_order)
    transition_analysis = _gait_transitions(contacts, leg_order, timestep_s=timestep)

    return {
        "gait_platform_version": 2,
        "scientific_scope": (
            "Computational gait post-processing only. This analysis does not "
            "run simulations, alter perturbations, or validate a biological "
            "Parkinson's disease mechanism."
        ),
        "supported_inputs": list(SUPPORTED_GAIT_INPUTS),
        "configuration": _config_as_dict(settings),
        "input": gait_input.as_metadata(),
        "leg_order": list(leg_order),
        "time_s": _json_float_list(time_s),
        "contact_analysis": {
            "contact_timeline": _contact_timeline(contacts, leg_order, time_s),
            "contact_raster": {
                "leg_order": list(leg_order),
                "samples": contact_matrix.T.astype(int).tolist(),
            },
            "footfall_events": stance_bouts,
            "stance_bouts": stance_bouts,
            "swing_bouts": swing_bouts,
            "duty_factor_by_leg": duty_factor,
            "transition_matrix_by_leg": {
                leg: _binary_transition_matrix(contacts[leg]) for leg in leg_order
            },
            "contact_symmetry": _left_right_symmetry(duty_factor, {}, {}),
        },
        "gait_analysis": {
            "stride_events": stride_events,
            "cadence_hz_by_leg": cadence,
            "stride_duration_s_by_leg": stride_duration,
            "stride_frequency_hz_by_leg": cadence,
            "stride_length_mm_by_leg": stride_length,
            "gait_cycle_by_leg": _gait_cycles(stride_events),
            "gait_symmetry": _left_right_symmetry(duty_factor, stride_duration, cadence),
            "gait_transition_detection": transition_analysis,
            "gait_entropy_bits": _json_float(_pattern_entropy(transition_analysis["patterns"])),
            "gait_stability": _gait_stability(contact_matrix),
        },
        "coordination_analysis": {
            "left_right": _left_right_coordination(contacts),
            "front_middle_hind": _front_middle_hind_coordination(contacts),
            "inter_leg_phase": phase,
            "tripod_coordination": _tripod_coordination(contacts, leg_order),
            "tetrapod_coordination": _tetrapod_coordination(contacts, leg_order),
            "coordination_matrix": _coordination_matrix(contacts, leg_order),
            "phase_locking": _phase_locking(phase),
            "cross_correlation": _cross_correlation(contacts, leg_order),
        },
        "joint_trajectory_summary": _trajectory_mapping_summary(joints),
        "foot_trajectory_summary": _trajectory_mapping_summary(foot_positions),
        "all_metrics_finite": _all_numbers_finite(
            {
                "duty_factor": duty_factor,
                "stride_duration": stride_duration,
                "stride_length": stride_length,
                "cadence": cadence,
                "phase": phase,
                "stability": _gait_stability(contact_matrix),
            }
        ),
    }


def _coerce_config(config: GaitAnalysisConfig | Mapping[str, Any] | None) -> GaitAnalysisConfig:
    if config is None:
        return GaitAnalysisConfig()
    if isinstance(config, GaitAnalysisConfig):
        return config
    return GaitAnalysisConfig(**dict(config))


def _config_as_dict(config: GaitAnalysisConfig) -> dict[str, Any]:
    return {
        "contact_threshold": _json_float(config.contact_threshold),
        "min_contact_duration_s": _json_float(config.min_contact_duration_s),
        "min_swing_duration_s": _json_float(config.min_swing_duration_s),
        "min_stride_duration_s": _json_float(config.min_stride_duration_s),
        "transition_smoothing_samples": int(config.transition_smoothing_samples),
        "phase_reference_legs": list(config.phase_reference_legs),
    }


def _ordered_legs(contacts: Mapping[str, np.ndarray]) -> tuple[str, ...]:
    known = [leg for leg in CANONICAL_LEG_ORDER if leg in contacts]
    extra = sorted(leg for leg in contacts if leg not in CANONICAL_LEG_ORDER)
    return tuple(known + extra)


def _segments_to_bouts(
    mask: np.ndarray,
    *,
    timestep_s: float,
    label: str,
    min_duration_s: float,
) -> list[dict[str, Any]]:
    bouts: list[dict[str, Any]] = []
    start: int | None = None
    for index, active in enumerate(mask):
        if active and start is None:
            start = index
        if start is not None and (not active or index == len(mask) - 1):
            end = index if not active else index + 1
            duration = (end - start) * timestep_s
            if duration >= min_duration_s:
                bouts.append(
                    {
                        "type": label,
                        "start_sample": int(start),
                        "end_sample_exclusive": int(end),
                        "start_time_s": _json_float(start * timestep_s),
                        "end_time_s": _json_float(end * timestep_s),
                        "duration_s": _json_float(duration),
                    }
                )
            start = None
    return bouts


def _stride_events(
    *,
    leg: str,
    stance_bouts: Sequence[Mapping[str, Any]],
    foot_positions: np.ndarray | None,
    timestep_s: float,
    min_stride_duration_s: float,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    onsets = [int(bout["start_sample"]) for bout in stance_bouts]
    for stride_index, (start, end) in enumerate(zip(onsets, onsets[1:])):
        duration = (end - start) * timestep_s
        if duration < min_stride_duration_s:
            continue
        stance = stance_bouts[stride_index]
        length = None
        if foot_positions is not None:
            length = float(np.linalg.norm(foot_positions[end, :2] - foot_positions[start, :2]))
        events.append(
            {
                "leg": leg,
                "stride_index": int(stride_index),
                "start_sample": int(start),
                "end_sample_exclusive": int(end),
                "start_time_s": _json_float(start * timestep_s),
                "end_time_s": _json_float(end * timestep_s),
                "duration_s": _json_float(duration),
                "frequency_hz": _json_float(1.0 / duration if duration > 0 else math.nan),
                "stance_duration_s": stance["duration_s"],
                "stance_fraction": _json_float(
                    float(stance["duration_s"]) / duration if duration > 0 else math.nan
                ),
                "stride_length_mm": _json_float(length) if length is not None else None,
            }
        )
    return events


def _gait_cycles(stride_events: Mapping[str, Sequence[Mapping[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    cycles: dict[str, list[dict[str, Any]]] = {}
    for leg, events in stride_events.items():
        cycles[leg] = [
            {
                "cycle_index": int(event["stride_index"]),
                "start_time_s": event["start_time_s"],
                "duration_s": event["duration_s"],
                "stance_fraction": event["stance_fraction"],
                "swing_fraction": _json_float(1.0 - float(event["stance_fraction"]))
                if event["stance_fraction"] is not None
                else None,
            }
            for event in events
        ]
    return cycles


def _contact_timeline(
    contacts: Mapping[str, np.ndarray],
    leg_order: Sequence[str],
    time_s: np.ndarray,
) -> list[dict[str, Any]]:
    rows = []
    for index, t_value in enumerate(time_s):
        active = [leg for leg in leg_order if contacts[leg][index]]
        rows.append(
            {
                "sample_index": int(index),
                "time_s": _json_float(t_value),
                "active_legs": active,
                "support_count": len(active),
                "pattern": _pattern_at(contacts, leg_order, index),
            }
        )
    return rows


def _binary_transition_matrix(mask: np.ndarray) -> dict[str, int]:
    matrix = {
        "inactive_to_inactive": 0,
        "inactive_to_active": 0,
        "active_to_inactive": 0,
        "active_to_active": 0,
    }
    for before, after in zip(mask[:-1], mask[1:]):
        if not before and not after:
            matrix["inactive_to_inactive"] += 1
        elif not before and after:
            matrix["inactive_to_active"] += 1
        elif before and not after:
            matrix["active_to_inactive"] += 1
        else:
            matrix["active_to_active"] += 1
    return matrix


def _left_right_symmetry(
    duty_factor: Mapping[str, float | None],
    stride_duration: Mapping[str, Mapping[str, Any]],
    cadence: Mapping[str, float | None],
) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for left, right in LEFT_RIGHT_PAIRS:
        if left not in duty_factor or right not in duty_factor:
            continue
        left_stride = stride_duration.get(left, {}).get("mean")
        right_stride = stride_duration.get(right, {}).get("mean")
        rows[f"{left}_{right}"] = {
            "duty_factor_delta_left_minus_right": _nullable_delta(
                duty_factor[left], duty_factor[right]
            ),
            "cadence_delta_left_minus_right_hz": _nullable_delta(
                cadence.get(left), cadence.get(right)
            ),
            "stride_duration_delta_left_minus_right_s": _nullable_delta(
                left_stride, right_stride
            ),
        }
    return rows


def _left_right_coordination(contacts: Mapping[str, np.ndarray]) -> dict[str, Any]:
    rows = {}
    for left, right in LEFT_RIGHT_PAIRS:
        if left in contacts and right in contacts:
            both = np.logical_and(contacts[left], contacts[right])
            either = np.logical_or(contacts[left], contacts[right])
            rows[f"{left}_{right}"] = {
                "co_contact_fraction": _json_float(np.mean(both)),
                "exclusive_contact_fraction": _json_float(np.mean(either & ~both)),
                "left_duty_factor": _json_float(np.mean(contacts[left])),
                "right_duty_factor": _json_float(np.mean(contacts[right])),
            }
    return rows


def _front_middle_hind_coordination(contacts: Mapping[str, np.ndarray]) -> dict[str, Any]:
    groups = {
        "front": [leg for leg in ("LF", "RF") if leg in contacts],
        "middle": [leg for leg in ("LM", "RM") if leg in contacts],
        "hind": [leg for leg in ("LH", "RH") if leg in contacts],
    }
    return {
        name: {
            "legs": legs,
            "mean_duty_factor": _json_float(np.mean([np.mean(contacts[leg]) for leg in legs]))
            if legs
            else None,
        }
        for name, legs in groups.items()
    }


def _inter_leg_phase(
    stride_events: Mapping[str, Sequence[Mapping[str, Any]]],
    leg_order: Sequence[str],
) -> dict[str, Any]:
    onsets = {
        leg: [int(event["start_sample"]) for event in events]
        for leg, events in stride_events.items()
    }
    phases: dict[str, Any] = {}
    for source in leg_order:
        source_onsets = onsets.get(source, [])
        if len(source_onsets) < 2:
            continue
        for target in leg_order:
            if source == target:
                continue
            target_onsets = onsets.get(target, [])
            values = []
            for start, end in zip(source_onsets, source_onsets[1:]):
                candidates = [value for value in target_onsets if start <= value < end]
                if candidates:
                    values.append((candidates[0] - start) / (end - start))
            if values:
                phases[f"{source}_to_{target}"] = {
                    "phase_fraction": _json_float_list(np.asarray(values, dtype=float)),
                    "mean_phase_fraction": _json_float(np.mean(values)),
                    "sample_count": len(values),
                }
    return phases


def _phase_locking(phase: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    locking = {}
    for pair, values in phase.items():
        samples = np.asarray(values.get("phase_fraction", []), dtype=float)
        if samples.size == 0:
            continue
        vectors = np.exp(2j * np.pi * samples)
        locking[pair] = {
            "mean_resultant_length": _json_float(abs(np.mean(vectors))),
            "mean_angle_rad": _json_float(float(np.angle(np.mean(vectors)))),
        }
    return locking


def _tripod_coordination(contacts: Mapping[str, np.ndarray], leg_order: Sequence[str]) -> dict[str, Any]:
    if not all(leg in contacts for leg in (*TRIPOD_A, *TRIPOD_B)):
        return {"available": False, "reason": "canonical six-leg contact data unavailable"}
    tripod_a = np.vstack([contacts[leg] for leg in TRIPOD_A])
    tripod_b = np.vstack([contacts[leg] for leg in TRIPOD_B])
    a_active = np.all(tripod_a, axis=0) & ~np.any(tripod_b, axis=0)
    b_active = np.all(tripod_b, axis=0) & ~np.any(tripod_a, axis=0)
    support_count = np.sum(np.vstack([contacts[leg] for leg in leg_order]), axis=0)
    return {
        "available": True,
        "tripod_a": list(TRIPOD_A),
        "tripod_b": list(TRIPOD_B),
        "exclusive_tripod_fraction": _json_float(np.mean(a_active | b_active)),
        "alternating_tripod_samples": int(np.count_nonzero(a_active | b_active)),
        "mean_support_count": _json_float(np.mean(support_count)),
    }


def _tetrapod_coordination(contacts: Mapping[str, np.ndarray], leg_order: Sequence[str]) -> dict[str, Any]:
    support_count = np.sum(np.vstack([contacts[leg] for leg in leg_order]), axis=0)
    return {
        "tetrapod_fraction": _json_float(np.mean(support_count == 4)),
        "tetrapod_samples": int(np.count_nonzero(support_count == 4)),
    }


def _coordination_matrix(contacts: Mapping[str, np.ndarray], leg_order: Sequence[str]) -> dict[str, Any]:
    rows = []
    for leg_a in leg_order:
        row = []
        for leg_b in leg_order:
            row.append(_json_float(_safe_corr(contacts[leg_a], contacts[leg_b])))
        rows.append(row)
    return {"leg_order": list(leg_order), "correlation": rows}


def _cross_correlation(contacts: Mapping[str, np.ndarray], leg_order: Sequence[str]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for index, leg_a in enumerate(leg_order):
        for leg_b in leg_order[index + 1 :]:
            corr, lag = _max_cross_correlation(contacts[leg_a], contacts[leg_b])
            values[f"{leg_a}_{leg_b}"] = {
                "max_correlation": _json_float(corr),
                "lag_samples": int(lag),
            }
    return values


def _gait_transitions(
    contacts: Mapping[str, np.ndarray],
    leg_order: Sequence[str],
    *,
    timestep_s: float,
) -> dict[str, Any]:
    patterns = [_pattern_at(contacts, leg_order, index) for index in range(next(iter(contacts.values())).size)]
    transitions = []
    for index, (before, after) in enumerate(zip(patterns[:-1], patterns[1:]), start=1):
        if before != after:
            transitions.append(
                {
                    "transition_index": len(transitions),
                    "sample_index": int(index),
                    "time_s": _json_float(index * timestep_s),
                    "from_pattern": before,
                    "to_pattern": after,
                }
            )
    return {
        "patterns": patterns,
        "transitions": transitions,
        "transition_count": len(transitions),
        "unique_pattern_count": len(set(patterns)),
    }


def _gait_stability(contact_matrix: np.ndarray) -> dict[str, Any]:
    support_count = np.sum(contact_matrix, axis=0)
    support_std = float(np.std(support_count))
    return {
        "support_count_mean": _json_float(np.mean(support_count)),
        "support_count_std": _json_float(support_std),
        "support_count_min": int(np.min(support_count)),
        "support_count_max": int(np.max(support_count)),
        "stability_index": _json_float(1.0 / (1.0 + support_std)),
        "at_least_three_contacts_fraction": _json_float(np.mean(support_count >= 3)),
    }


def _pattern_at(contacts: Mapping[str, np.ndarray], leg_order: Sequence[str], index: int) -> str:
    return "".join("1" if contacts[leg][index] else "0" for leg in leg_order)


def _pattern_entropy(patterns: Sequence[str]) -> float:
    if not patterns:
        return 0.0
    _, counts = np.unique(np.asarray(patterns), return_counts=True)
    probabilities = counts / counts.sum()
    return float(-np.sum(probabilities * np.log2(probabilities)))


def _trajectory_mapping_summary(values: Mapping[str, np.ndarray]) -> dict[str, Any]:
    return {
        "available": bool(values),
        "trajectory_count": len(values),
        "trajectories": {
            name: {
                "shape": list(array.shape),
                "min": _json_float(np.min(array)),
                "max": _json_float(np.max(array)),
                "mean": _json_float(np.mean(array)),
                "absolute_mean": _json_float(np.mean(np.abs(array))),
            }
            for name, array in values.items()
        },
    }


def _summary(values: Sequence[Any]) -> dict[str, Any]:
    clean = [float(value) for value in values if value is not None and np.isfinite(float(value))]
    if not clean:
        return {"count": 0, "min": None, "max": None, "mean": None, "std": None}
    array = np.asarray(clean, dtype=float)
    return {
        "count": int(array.size),
        "min": _json_float(np.min(array)),
        "max": _json_float(np.max(array)),
        "mean": _json_float(np.mean(array)),
        "std": _json_float(np.std(array)),
    }


def _duration_s(sample_count: int, timestep_s: float) -> float:
    return max(float(sample_count - 1) * timestep_s, timestep_s)


def _nullable_delta(left: Any, right: Any) -> float | None:
    if left is None or right is None:
        return None
    return _json_float(float(left) - float(right))


def _safe_corr(left: np.ndarray, right: np.ndarray) -> float:
    a = left.astype(float)
    b = right.astype(float)
    if a.size != b.size:
        raise ValueError("correlation arrays must share sample count.")
    if np.std(a) == 0 or np.std(b) == 0:
        return 1.0 if np.array_equal(a, b) else 0.0
    return float(np.corrcoef(a, b)[0, 1])


def _max_cross_correlation(left: np.ndarray, right: np.ndarray) -> tuple[float, int]:
    a = left.astype(float) - np.mean(left)
    b = right.astype(float) - np.mean(right)
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return (_safe_corr(left, right), 0)
    corr = np.correlate(a, b, mode="full") / denom
    lags = np.arange(-len(left) + 1, len(left))
    index = int(np.argmax(np.abs(corr)))
    return float(corr[index]), int(lags[index])


def _matrix_mapping(values: Mapping[str, ArrayLike], name: str, *, width: int) -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for key, value in values.items():
        array = np.asarray(value, dtype=float)
        if array.ndim != 2 or array.shape[1] != width:
            raise ValueError(f"{name}[{key!r}] must have shape (n_samples, {width}).")
        if array.shape[0] == 0 or not np.isfinite(array).all():
            raise ValueError(f"{name}[{key!r}] must contain finite samples.")
        arrays[str(key)] = array
    return arrays


def _validate_equal_sample_counts(values: Mapping[str, np.ndarray], name: str) -> None:
    if not values:
        raise ValueError(f"{name} must include at least one leg.")
    counts = {array.shape[0] for array in values.values()}
    if len(counts) != 1:
        raise ValueError(f"{name} sample counts must match.")


def _json_float(value: Any) -> float | None:
    result = float(value)
    return result if math.isfinite(result) else None


def _json_float_list(values: np.ndarray) -> list[float | None]:
    return [_json_float(value) for value in np.asarray(values, dtype=float).ravel()]


def _all_numbers_finite(value: Any) -> bool:
    if isinstance(value, dict):
        return all(_all_numbers_finite(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return all(_all_numbers_finite(item) for item in value)
    if isinstance(value, (str, bool)) or value is None:
        return True
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return True


__all__ = [
    "CANONICAL_LEG_ORDER",
    "LEFT_RIGHT_PAIRS",
    "SUPPORTED_GAIT_INPUTS",
    "TRIPOD_A",
    "TRIPOD_B",
    "GaitAnalysisConfig",
    "GaitInput",
    "analyze_gait",
]
