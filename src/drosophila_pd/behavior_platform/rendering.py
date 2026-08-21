"""Offline rendering for v2 rollout visualizations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drosophila_pd.behavior_platform.rollout import RolloutData


SUPPORTED_RENDER_FORMATS = ("mp4", "gif", "png_sequence")


@dataclass(frozen=True)
class OfflineRenderRequest:
    output_dir: Path | str
    format: str = "png_sequence"
    fps: int = 20
    stride: int = 1
    include_heading: bool = True


@dataclass(frozen=True)
class OfflineRenderResult:
    format: str
    files: tuple[Path, ...]
    frame_count: int
    backend: str
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "files": [str(path) for path in self.files],
            "frame_count": self.frame_count,
            "backend": self.backend,
            "notes": list(self.notes),
        }


def render_offline(
    rollout: RolloutData | Sequence[RolloutData],
    request: OfflineRenderRequest,
) -> OfflineRenderResult:
    """Render rollout trajectory frames or animations without running simulation."""

    rollouts = (rollout,) if isinstance(rollout, RolloutData) else tuple(rollout)
    if not rollouts:
        raise ValueError("at least one rollout is required.")
    fmt = request.format.lower()
    if fmt not in SUPPORTED_RENDER_FORMATS:
        raise ValueError(f"unsupported render format: {request.format}")
    stride = int(request.stride)
    if stride <= 0:
        raise ValueError("stride must be a positive integer.")
    fps = int(request.fps)
    if fps <= 0:
        raise ValueError("fps must be a positive integer.")

    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_paths = _render_png_sequence(
        rollouts,
        output_dir / "frames",
        stride=stride,
        include_heading=request.include_heading,
    )
    if fmt == "png_sequence":
        return OfflineRenderResult(
            format=fmt,
            files=tuple(frame_paths),
            frame_count=len(frame_paths),
            backend="matplotlib_png",
        )
    animation_path = output_dir / ("comparison.mp4" if fmt == "mp4" else "comparison.gif")
    try:
        _encode_animation(frame_paths, animation_path, fps=fps)
        files = (animation_path,)
        notes: tuple[str, ...] = ()
    except RuntimeError as exc:
        files = tuple(frame_paths)
        notes = (str(exc), "PNG sequence was retained as the deterministic fallback.")
    return OfflineRenderResult(
        format=fmt,
        files=files,
        frame_count=len(frame_paths),
        backend="imageio_or_png_fallback",
        notes=notes,
    )


def _render_png_sequence(
    rollouts: Sequence[RolloutData],
    output_dir: Path,
    *,
    stride: int,
    include_heading: bool,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    max_samples = max(rollout.sample_count() for rollout in rollouts)
    positions = [rollout.positions_array() for rollout in rollouts]
    labels = [rollout.condition_id for rollout in rollouts]
    x_all = np.concatenate([pos[:, 0] for pos in positions])
    y_all = np.concatenate([pos[:, 1] for pos in positions])
    margin = max(1.0, 0.05 * max(np.ptp(x_all) or 1.0, np.ptp(y_all) or 1.0))

    frame_paths: list[Path] = []
    for frame_index in range(0, max_samples, stride):
        fig, ax = plt.subplots(figsize=(6, 5), constrained_layout=True)
        for pos, label in zip(positions, labels):
            last = min(frame_index + 1, pos.shape[0])
            ax.plot(pos[:last, 0], pos[:last, 1], linewidth=2, label=label)
            ax.scatter([pos[last - 1, 0]], [pos[last - 1, 1]], s=28)
            if include_heading and last > 1:
                delta = pos[last - 1, :2] - pos[max(0, last - 2), :2]
                ax.arrow(
                    pos[last - 1, 0],
                    pos[last - 1, 1],
                    delta[0],
                    delta[1],
                    head_width=0.4,
                    length_includes_head=True,
                )
        ax.set_xlim(float(np.min(x_all) - margin), float(np.max(x_all) + margin))
        ax.set_ylim(float(np.min(y_all) - margin), float(np.max(y_all) + margin))
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlabel("x (mm)")
        ax.set_ylabel("y (mm)")
        ax.set_title(f"Frame {frame_index}")
        ax.legend(loc="best")
        path = output_dir / f"frame_{frame_index:05d}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        frame_paths.append(path)
    return frame_paths


def _encode_animation(frame_paths: Sequence[Path], output_path: Path, *, fps: int) -> None:
    try:
        import imageio.v2 as imageio
    except Exception as exc:  # pragma: no cover - depends on optional backend
        raise RuntimeError("imageio is unavailable for MP4/GIF encoding.") from exc
    frames = [imageio.imread(path) for path in frame_paths]
    try:
        imageio.mimsave(output_path, frames, fps=fps)
    except Exception as exc:  # pragma: no cover - backend specific
        raise RuntimeError(f"animation encoding failed: {exc}") from exc


__all__ = [
    "SUPPORTED_RENDER_FORMATS",
    "OfflineRenderRequest",
    "OfflineRenderResult",
    "render_offline",
]
