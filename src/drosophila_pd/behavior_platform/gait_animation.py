"""Animation export for v2 gait-analysis packages."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from drosophila_pd.behavior_platform.gait import GaitInput, analyze_gait


SUPPORTED_GAIT_ANIMATION_FORMATS = ("png_sequence", "gif", "mp4")


@dataclass(frozen=True)
class GaitAnimationRequest:
    output_dir: Path | str
    format: str = "png_sequence"
    fps: int = 20
    stride: int = 1


@dataclass(frozen=True)
class GaitAnimationResult:
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


def render_gait_animation(
    gait_input: GaitInput | Sequence[GaitInput],
    request: GaitAnimationRequest,
) -> GaitAnimationResult:
    """Render gait contact timelines as PNG frames, GIF, or MP4."""

    inputs = (gait_input,) if isinstance(gait_input, GaitInput) else tuple(gait_input)
    if not inputs:
        raise ValueError("at least one gait input is required.")
    fmt = request.format.lower()
    if fmt not in SUPPORTED_GAIT_ANIMATION_FORMATS:
        raise ValueError(f"unsupported gait animation format: {request.format}")
    fps = int(request.fps)
    stride = int(request.stride)
    if fps <= 0:
        raise ValueError("fps must be a positive integer.")
    if stride <= 0:
        raise ValueError("stride must be a positive integer.")

    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    frame_paths = _render_contact_frames(inputs, output_dir / "frames", stride=stride)
    if fmt == "png_sequence":
        return GaitAnimationResult(
            format=fmt,
            files=tuple(frame_paths),
            frame_count=len(frame_paths),
            backend="matplotlib_png",
        )
    animation_path = output_dir / ("gait.mp4" if fmt == "mp4" else "gait.gif")
    try:
        _encode_animation(frame_paths, animation_path, fps=fps)
        files = (animation_path,)
        notes: tuple[str, ...] = ()
    except RuntimeError as exc:
        files = tuple(frame_paths)
        notes = (str(exc), "PNG sequence was retained as the deterministic fallback.")
    return GaitAnimationResult(
        format=fmt,
        files=files,
        frame_count=len(frame_paths),
        backend="imageio_or_png_fallback",
        notes=notes,
    )


def _render_contact_frames(
    gait_inputs: Sequence[GaitInput],
    output_dir: Path,
    *,
    stride: int,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    reports = [analyze_gait(item) for item in gait_inputs]
    contacts = [
        np.asarray(report["contact_analysis"]["contact_raster"]["samples"], dtype=float).T
        for report in reports
    ]
    max_samples = max(matrix.shape[1] for matrix in contacts)
    frame_paths: list[Path] = []
    for frame_index in range(0, max_samples, stride):
        fig, axes = plt.subplots(
            len(gait_inputs),
            1,
            figsize=(8, max(3, 2.4 * len(gait_inputs))),
            squeeze=False,
            constrained_layout=True,
        )
        for row, (report, matrix) in enumerate(zip(reports, contacts)):
            ax = axes[row, 0]
            end = min(frame_index + 1, matrix.shape[1])
            ax.imshow(matrix[:, :end], aspect="auto", cmap="Greys", interpolation="nearest")
            ax.axvline(end - 1, color="#d62728", linewidth=1.5)
            ax.set_yticks(range(len(report["leg_order"])))
            ax.set_yticklabels(report["leg_order"])
            ax.set_title(report["input"]["condition_id"])
            ax.set_xlabel("sample")
        path = output_dir / f"gait_frame_{frame_index:05d}.png"
        fig.savefig(path, dpi=120)
        plt.close(fig)
        frame_paths.append(path)
    return frame_paths


def _encode_animation(frame_paths: Sequence[Path], output_path: Path, *, fps: int) -> None:
    try:
        import imageio.v2 as imageio
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("imageio is unavailable for gait animation encoding.") from exc
    frames = [imageio.imread(path) for path in frame_paths]
    try:
        imageio.mimsave(output_path, frames, fps=fps)
    except Exception as exc:  # pragma: no cover - backend specific
        raise RuntimeError(f"gait animation encoding failed: {exc}") from exc


__all__ = [
    "SUPPORTED_GAIT_ANIMATION_FORMATS",
    "GaitAnimationRequest",
    "GaitAnimationResult",
    "render_gait_animation",
]
