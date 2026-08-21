"""Synchronized behavior playback exports for Session08."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData


VIDEO_EXPORT_FORMATS = ("png_sequence", "gif", "mp4")


@dataclass(frozen=True)
class PlaybackOverlayConfig:
    trajectory: bool = True
    speed: bool = True
    heading: bool = True
    gait: bool = True
    contact: bool = True
    metadata: bool = True
    timestamp: bool = True


@dataclass(frozen=True)
class SynchronizedPlaybackRequest:
    output_dir: Path | str
    format: str = "png_sequence"
    layout: str = "split_screen"
    fps: int = 20
    stride: int = 1
    overlays: PlaybackOverlayConfig = PlaybackOverlayConfig()


@dataclass(frozen=True)
class SynchronizedPlaybackResult:
    format: str
    layout: str
    files: tuple[Path, ...]
    frame_count: int
    backend: str
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "layout": self.layout,
            "files": [str(path) for path in self.files],
            "frame_count": self.frame_count,
            "backend": self.backend,
            "notes": list(self.notes),
        }


def render_synchronized_playback(
    rollouts: Mapping[str, RolloutData],
    request: SynchronizedPlaybackRequest,
    *,
    contact_reports: Mapping[str, Mapping[str, Any]] | None = None,
) -> SynchronizedPlaybackResult:
    """Render synchronized Healthy/Candidate/Progression playback."""

    if len(rollouts) < 2:
        raise ValueError("at least two rollout conditions are required.")
    fmt = request.format.lower()
    if fmt not in VIDEO_EXPORT_FORMATS:
        raise ValueError(f"unsupported playback format: {request.format}")
    fps = int(request.fps)
    stride = int(request.stride)
    if fps <= 0:
        raise ValueError("fps must be a positive integer.")
    if stride <= 0:
        raise ValueError("stride must be a positive integer.")
    output = Path(request.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    frames = _render_frames(
        rollouts,
        output / "frames",
        stride=stride,
        layout=request.layout,
        overlays=request.overlays,
        contact_reports=contact_reports or {},
    )
    if fmt == "png_sequence":
        return SynchronizedPlaybackResult(
            format=fmt,
            layout=request.layout,
            files=tuple(frames),
            frame_count=len(frames),
            backend="matplotlib_png",
        )
    animation_path = output / ("behavior_playback.mp4" if fmt == "mp4" else "behavior_playback.gif")
    try:
        _encode_animation(frames, animation_path, fps=fps)
        files = (animation_path,)
        notes: tuple[str, ...] = ()
    except RuntimeError as exc:
        files = tuple(frames)
        notes = (str(exc), "PNG sequence was retained as the deterministic fallback.")
    return SynchronizedPlaybackResult(
        format=fmt,
        layout=request.layout,
        files=files,
        frame_count=len(frames),
        backend="imageio_or_png_fallback",
        notes=notes,
    )


def _render_frames(
    rollouts: Mapping[str, RolloutData],
    output_dir: Path,
    *,
    stride: int,
    layout: str,
    overlays: PlaybackOverlayConfig,
    contact_reports: Mapping[str, Mapping[str, Any]],
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    names = list(rollouts)
    positions = {name: rollout.positions_array() for name, rollout in rollouts.items()}
    max_samples = max(values.shape[0] for values in positions.values())
    cols = 2 if layout in {"split_screen", "quad_view"} else 1
    rows = int(np.ceil(len(names) / cols))
    frames: list[Path] = []
    for frame_index in range(0, max_samples, stride):
        fig, axes = plt.subplots(rows, cols, figsize=(6 * cols, 4 * rows), squeeze=False, constrained_layout=True)
        for ax in axes.ravel():
            ax.axis("off")
        for panel_index, name in enumerate(names):
            ax = axes.ravel()[panel_index]
            ax.axis("on")
            pos = positions[name]
            end = min(frame_index + 1, pos.shape[0])
            if overlays.trajectory:
                ax.plot(pos[:end, 0], pos[:end, 1], linewidth=2)
            ax.scatter([pos[end - 1, 0]], [pos[end - 1, 1]], s=28)
            if overlays.heading and end > 1:
                delta = pos[end - 1, :2] - pos[max(0, end - 2), :2]
                ax.arrow(pos[end - 1, 0], pos[end - 1, 1], delta[0], delta[1], head_width=0.2)
            title = name
            if overlays.timestamp:
                title += f" | t={rollouts[name].time_s()[end - 1]:.3f}s"
            ax.set_title(title)
            ax.set_aspect("equal", adjustable="box")
            ax.set_xlabel("x (mm)")
            ax.set_ylabel("y (mm)")
            if overlays.contact and name in contact_reports:
                ax.text(0.02, 0.02, "contact overlay", transform=ax.transAxes, fontsize=8)
            if overlays.metadata:
                ax.text(0.02, 0.92, f"samples={pos.shape[0]}", transform=ax.transAxes, fontsize=8)
        path = output_dir / f"playback_frame_{frame_index:05d}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        frames.append(path)
    return frames


def _encode_animation(frame_paths: Sequence[Path], output_path: Path, *, fps: int) -> None:
    try:
        import imageio.v2 as imageio
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("imageio is unavailable for behavior playback encoding.") from exc
    frames = [imageio.imread(path) for path in frame_paths]
    try:
        imageio.mimsave(output_path, frames, fps=fps)
    except Exception as exc:  # pragma: no cover - backend specific
        raise RuntimeError(f"behavior playback encoding failed: {exc}") from exc


__all__ = [
    "PlaybackOverlayConfig",
    "SynchronizedPlaybackRequest",
    "SynchronizedPlaybackResult",
    "VIDEO_EXPORT_FORMATS",
    "render_synchronized_playback",
]
