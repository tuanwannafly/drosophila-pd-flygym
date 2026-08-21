"""Configurable computational progression timelines for Session08."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from drosophila_pd.behavior_platform.data_model import ProgressionStage, ProgressionTimeline


def progression_from_config(config: Mapping[str, Any] | str | Path) -> ProgressionTimeline:
    """Load a progression timeline from a mapping or JSON file path."""

    data = _load_config(config)
    stages = tuple(
        ProgressionStage(
            name=str(stage["name"]),
            index=int(stage.get("index", index)),
            computational_parameters=dict(stage.get("computational_parameters", {})),
            metadata=dict(stage.get("metadata", {})),
        )
        for index, stage in enumerate(data["stages"])
    )
    times = tuple(float(value) for value in data.get("stage_times_s", range(len(stages))))
    timeline = ProgressionTimeline(
        timeline_id=str(data.get("timeline_id", "computational_progression")),
        stages=stages,
        stage_times_s=times,
        metadata=dict(data.get("metadata", {})),
    )
    _validate_timeline(timeline)
    return timeline


def stage_at(timeline: ProgressionTimeline, time_s: float) -> ProgressionStage:
    """Return the nearest stage at or before ``time_s``."""

    _validate_timeline(timeline)
    value = float(time_s)
    selected = timeline.stages[0]
    for stage, stage_time in zip(timeline.stages, timeline.stage_times_s):
        if value >= stage_time:
            selected = stage
    return selected


def interpolate_stages(
    left: ProgressionStage,
    right: ProgressionStage,
    fraction: float,
    *,
    name: str = "interpolated",
) -> ProgressionStage:
    """Interpolate numeric computational parameters between two stages."""

    alpha = min(1.0, max(0.0, float(fraction)))
    keys = sorted(set(left.computational_parameters) | set(right.computational_parameters))
    params: dict[str, Any] = {}
    for key in keys:
        a = left.computational_parameters.get(key)
        b = right.computational_parameters.get(key)
        if _is_number(a) and _is_number(b):
            params[key] = float(a) + alpha * (float(b) - float(a))
        else:
            params[key] = b if alpha >= 0.5 else a
    return ProgressionStage(
        name=name,
        index=-1,
        computational_parameters=params,
        metadata={
            "interpolation_fraction": alpha,
            "left_stage": left.name,
            "right_stage": right.name,
            "scientific_scope": "Computational parameter interpolation only.",
        },
    )


def interpolated_stage_at(timeline: ProgressionTimeline, time_s: float) -> ProgressionStage:
    """Return an interpolated stage for a continuous progression time."""

    _validate_timeline(timeline)
    value = float(time_s)
    if value <= timeline.stage_times_s[0]:
        return timeline.stages[0]
    if value >= timeline.stage_times_s[-1]:
        return timeline.stages[-1]
    for index in range(len(timeline.stages) - 1):
        left_time = float(timeline.stage_times_s[index])
        right_time = float(timeline.stage_times_s[index + 1])
        if left_time <= value <= right_time:
            fraction = (value - left_time) / (right_time - left_time)
            return interpolate_stages(
                timeline.stages[index],
                timeline.stages[index + 1],
                fraction,
                name=f"{timeline.stages[index].name}_to_{timeline.stages[index + 1].name}",
            )
    return timeline.stages[-1]


def replay_progression(
    timeline: ProgressionTimeline,
    *,
    sample_times_s: list[float] | tuple[float, ...],
    interpolate: bool = True,
) -> dict[str, Any]:
    """Create a reproducible progression replay record."""

    stages = [
        (interpolated_stage_at(timeline, value) if interpolate else stage_at(timeline, value)).as_dict()
        for value in sample_times_s
    ]
    return {
        "progression_version": 2,
        "scientific_scope": (
            "Progression stages store computational parameters only and do not "
            "encode biological disease stages."
        ),
        "timeline": timeline.as_dict(),
        "sample_times_s": [float(value) for value in sample_times_s],
        "interpolate": bool(interpolate),
        "replayed_stages": stages,
    }


def progression_to_json(timeline: ProgressionTimeline, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(timeline.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
    return path


def _load_config(config: Mapping[str, Any] | str | Path) -> Mapping[str, Any]:
    if isinstance(config, Mapping):
        return config
    return json.loads(Path(config).read_text(encoding="utf-8"))


def _validate_timeline(timeline: ProgressionTimeline) -> None:
    if not timeline.stages:
        raise ValueError("progression timeline requires at least one stage.")
    if len(timeline.stages) != len(timeline.stage_times_s):
        raise ValueError("stage_times_s length must match stages length.")
    times = [float(value) for value in timeline.stage_times_s]
    if times != sorted(times):
        raise ValueError("stage_times_s must be sorted.")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


__all__ = [
    "interpolate_stages",
    "interpolated_stage_at",
    "progression_from_config",
    "progression_to_json",
    "replay_progression",
    "stage_at",
]
