"""Visualization plans and static overlays for v2 behavioral rollouts."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData


@dataclass(frozen=True)
class CameraPreset:
    name: str
    distance: float
    azimuth_deg: float
    elevation_deg: float
    lookat_xyz_mm: tuple[float, float, float] = (0.0, 0.0, 1.0)

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "distance": self.distance,
            "azimuth_deg": self.azimuth_deg,
            "elevation_deg": self.elevation_deg,
            "lookat_xyz_mm": list(self.lookat_xyz_mm),
        }


DEFAULT_CAMERA_PRESETS = (
    CameraPreset("top", distance=80.0, azimuth_deg=0.0, elevation_deg=-90.0),
    CameraPreset("side", distance=60.0, azimuth_deg=90.0, elevation_deg=0.0),
    CameraPreset("follow", distance=35.0, azimuth_deg=135.0, elevation_deg=-25.0),
)


@dataclass(frozen=True)
class ViewerPlan:
    viewer_type: str
    camera_presets: tuple[CameraPreset, ...]
    overlays: tuple[str, ...]
    timeline: dict[str, Any]
    controls: tuple[str, ...] = ("pause", "replay", "step", "scrub")
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "viewer_type": self.viewer_type,
            "camera_presets": [preset.as_dict() for preset in self.camera_presets],
            "overlays": list(self.overlays),
            "timeline": dict(self.timeline),
            "controls": list(self.controls),
            "notes": list(self.notes),
        }


def build_viewer_plan(
    rollout: RolloutData,
    *,
    viewer_type: str = "interactive_mujoco",
    camera_presets: tuple[CameraPreset, ...] = DEFAULT_CAMERA_PRESETS,
) -> ViewerPlan:
    """Build a deterministic viewer plan without opening a MuJoCo viewer."""

    return ViewerPlan(
        viewer_type=viewer_type,
        camera_presets=camera_presets,
        overlays=(
            "trajectory",
            "heading",
            "center_of_mass",
            "joint_state",
            "adhesion_state",
            "timeline",
        ),
        timeline={
            "sample_count": rollout.sample_count(),
            "timestep_s": rollout.timestep(),
            "duration_s": (rollout.sample_count() - 1) * rollout.timestep(),
            "synchronized": True,
        },
        notes=(
            "This plan describes viewer configuration only.",
            "Opening an interactive MuJoCo viewer requires a runtime with MuJoCo.",
        ),
    )


def plot_rollout_summary(
    rollout: RolloutData,
    measurements: dict[str, Any],
    output_path: str | Path,
) -> Path:
    """Write a static PNG with trajectory, heading, speed, and turning overlays."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    positions = rollout.positions_array()
    time_s = np.asarray(measurements["trajectory"]["time_s"], dtype=float)
    speed = np.asarray(measurements["trajectory"]["instantaneous_speed_mm_s"], dtype=float)
    heading = np.asarray(measurements["heading_rad"], dtype=float)
    yaw_rate = np.asarray(measurements["yaw_rate_rad_s"], dtype=float)

    fig, axes = plt.subplots(2, 2, figsize=(10, 7), constrained_layout=True)
    ax = axes[0, 0]
    ax.plot(positions[:, 0], positions[:, 1], color="#1f77b4", linewidth=2)
    ax.scatter([positions[0, 0]], [positions[0, 1]], color="#2ca02c", label="start")
    ax.scatter([positions[-1, 0]], [positions[-1, 1]], color="#d62728", label="end")
    ax.set_title("Trajectory")
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.axis("equal")
    ax.legend(loc="best")

    axes[0, 1].plot(time_s, heading, color="#9467bd")
    axes[0, 1].set_title("Heading")
    axes[0, 1].set_xlabel("time (s)")
    axes[0, 1].set_ylabel("rad")

    axes[1, 0].plot(time_s, speed, color="#ff7f0e")
    axes[1, 0].set_title("Instantaneous Speed")
    axes[1, 0].set_xlabel("time (s)")
    axes[1, 0].set_ylabel("mm/s")

    yaw_time = time_s[1:] if time_s.size > 1 else np.array([], dtype=float)
    axes[1, 1].plot(yaw_time, yaw_rate, color="#8c564b")
    axes[1, 1].set_title("Yaw Rate")
    axes[1, 1].set_xlabel("time (s)")
    axes[1, 1].set_ylabel("rad/s")

    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


__all__ = [
    "DEFAULT_CAMERA_PRESETS",
    "CameraPreset",
    "ViewerPlan",
    "build_viewer_plan",
    "plot_rollout_summary",
]
