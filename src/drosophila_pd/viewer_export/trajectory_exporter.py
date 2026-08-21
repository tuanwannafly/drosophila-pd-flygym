"""Build per-frame trajectory payloads from imported rollout arrays."""

from __future__ import annotations

from typing import Any, Mapping

import numpy as np


def build_trajectory_frames(
    thorax_positions: np.ndarray,
    *,
    com_positions: np.ndarray | None,
    joint_positions: Mapping[str, np.ndarray],
) -> list[dict[str, Any]]:
    """Return JSON-ready trajectory data without creating missing samples."""

    positions = np.asarray(thorax_positions, dtype=float)
    count = int(positions.shape[0])
    com = None if com_positions is None else np.asarray(com_positions, dtype=float)
    frames: list[dict[str, Any]] = []
    for index in range(count):
        frame: dict[str, Any] = {"thorax": positions[index].tolist()}
        if com is not None:
            frame["COM"] = com[index].tolist()
        if joint_positions:
            frame["joints"] = {
                name: _json_value(values[index]) for name, values in joint_positions.items()
            }
        frames.append(frame)
    return frames


def trajectory_for_frame(
    index: int,
    *,
    thorax: np.ndarray,
    com: np.ndarray | None,
    joint_positions: Mapping[str, np.ndarray],
) -> dict[str, Any]:
    """Build one trajectory record for callers that stream frame assembly."""

    value: dict[str, Any] = {"thorax": np.asarray(thorax, dtype=float).tolist()}
    if com is not None:
        value["COM"] = np.asarray(com, dtype=float).tolist()
    if joint_positions:
        value["joints"] = {
            name: _json_value(series[index]) for name, series in joint_positions.items()
        }
    return value


def _json_value(value: Any) -> Any:
    array = np.asarray(value)
    if array.ndim == 0:
        return array.item()
    return array.tolist()


__all__ = ["build_trajectory_frames", "trajectory_for_frame"]
