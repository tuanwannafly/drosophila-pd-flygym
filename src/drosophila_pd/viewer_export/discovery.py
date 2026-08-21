"""Filesystem discovery helpers for rollout, pose, and viewer bundle artifacts."""

from __future__ import annotations

from pathlib import Path


_IGNORED_DIRECTORIES = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".venv",
    "venv",
    "build",
    "node_modules",
}


def _files_named(root: Path, filename: str) -> list[Path]:
    root = root.expanduser().resolve()
    if not root.exists():
        return []
    if root.is_file():
        return [root] if root.name == filename else []
    paths = []
    for path in root.rglob(filename):
        if any(part in _IGNORED_DIRECTORIES for part in path.parts):
            continue
        if path.is_file():
            paths.append(path)
    return paths


def _latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda path: (path.stat().st_mtime_ns, path.as_posix()))


def find_latest_rollout(root: str | Path = ".") -> Path | None:
    """Return the newest usable ``rollout.json`` artifact.

    A rollout is usable when its directory also contains either the canonical
    ``rollout.npz`` or the legacy ``rollout_arrays.npz`` filename.
    """

    candidates = []
    for path in _files_named(Path(root), "rollout.json"):
        parent = path.parent
        if (parent / "rollout.npz").is_file() or (parent / "rollout_arrays.npz").is_file():
            candidates.append(path)
    return _latest(candidates)


def find_latest_viewer_pose(root: str | Path = ".") -> Path | None:
    """Return the newest ``viewer_pose.json`` below ``root``."""

    return _latest(_files_named(Path(root), "viewer_pose.json"))


def find_latest_bundle(root: str | Path = ".") -> Path | None:
    """Return the newest ``viewer_bundle.zip`` below ``root``."""

    return _latest(_files_named(Path(root), "viewer_bundle.zip"))


__all__ = ["find_latest_bundle", "find_latest_rollout", "find_latest_viewer_pose"]
