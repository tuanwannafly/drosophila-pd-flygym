"""Build a self-contained static bundle for the Fly Studio pose viewer."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys
from typing import Any, Iterable
import zipfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from drosophila_pd.viewer_export.discovery import find_latest_viewer_pose  # noqa: E402

DEFAULT_WEB_ROOT = REPOSITORY_ROOT / "web"
DEFAULT_OUTPUT = REPOSITORY_ROOT / "dist" / "viewer_bundle.zip"


class ViewerBundleError(RuntimeError):
    """Raised when a viewer bundle cannot be built safely."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_viewer_pose(path: str | Path | None = None, *, repo_root: Path = REPOSITORY_ROOT) -> Path:
    """Resolve an explicit pose or the only discovered pose artifact."""

    if path is not None:
        pose = Path(path).expanduser().resolve()
        if not pose.is_file():
            raise ViewerBundleError(f"viewer_pose.json was not found: {pose}")
        return pose

    pose = find_latest_viewer_pose(repo_root)
    if pose is None:
        raise ViewerBundleError(
            "No viewer_pose.json was found. Pass --pose PATH after exporting the viewer pose."
        )
    return pose


def _load_pose(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ViewerBundleError(f"Unable to read viewer pose {path}: {exc}") from exc

    source_root = REPOSITORY_ROOT / "src"
    if str(source_root) not in sys.path:
        sys.path.insert(0, str(source_root))
    try:
        from drosophila_pd.viewer_export import validate_pose_document
        validate_pose_document(document)
    except Exception as exc:
        raise ViewerBundleError(f"viewer_pose.json failed validation: {exc}") from exc
    return document


def _safe_asset_uri(uri: str) -> Path:
    candidate = PurePosixPath(uri)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ViewerBundleError(f"Mesh asset URI must be a relative path: {uri}")
    return Path(*candidate.parts)


def _copy_local_mesh_asset(
    document: dict[str, Any],
    pose_path: Path,
    stage: Path,
    web_root: Path,
) -> None:
    mesh = document.get("mesh")
    asset = mesh.get("asset") if isinstance(mesh, dict) else None
    if not isinstance(asset, dict):
        return
    uri = asset.get("uri")
    if not isinstance(uri, str) or not uri or "://" in uri:
        return

    relative_uri = _safe_asset_uri(uri)
    sources = (
        pose_path.parent / relative_uri,
        web_root / relative_uri,
        REPOSITORY_ROOT / relative_uri,
    )
    source = next((candidate for candidate in sources if candidate.is_file()), None)
    if source is None:
        raise ViewerBundleError(f"Mesh asset declared by viewer_pose.json was not found: {uri}")

    destination = stage / relative_uri
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_optional_source_metadata(pose_path: Path, stage: Path) -> None:
    """Preserve dataset provenance without replacing the bundle manifest."""

    for source_name, bundle_name in (("manifest.json", "rollout_manifest.json"), ("metadata.json", "metadata.json")):
        source = pose_path.parent / source_name
        if source.is_file():
            shutil.copy2(source, stage / bundle_name)


def _write_entrypoint(stage: Path) -> None:
    index = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Fly Studio Viewer</title>
  <link rel="stylesheet" href="./theme.css">
  <script type="importmap">
  {
    "imports": {
      "three": "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js",
      "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/"
    }
  }
  </script>
  <style>
    html, body { margin: 0; min-height: 100%; background: #0b0f14; color: #edf2f7; }
    #viewer { min-height: 100vh; }
    #status { padding: 0.75rem 1rem; font: 500 0.9rem/1.4 system-ui, sans-serif; }
    #status.error { color: #ffb4b4; }
  </style>
</head>
<body>
  <div id="status">Loading viewer_pose.json...</div>
  <main id="viewer" aria-label="Fly Studio viewer"></main>
  <script type="module">
    const status = document.getElementById('status');
    try {
      const { Viewer } = await import('./viewer/viewer.js');
      const response = await fetch(`./viewer_pose.json?cache=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`viewer_pose.json HTTP ${response.status}`);
      const pose = await response.json();
      const viewer = new Viewer();
      viewer.init(document.getElementById('viewer'));
      await viewer.loadPose(pose);
      window.flyStudioViewer = viewer;
      status.textContent = `Loaded ${pose.frame_count} frames`;
    } catch (error) {
      status.classList.add('error');
      status.textContent = `Viewer error: ${error.message}`;
      console.error('Fly Studio viewer failed:', error);
    }
  </script>
</body>
</html>
"""
    (stage / "index.html").write_text(index, encoding="utf-8")


def _copy_web_runtime(web_root: Path, stage: Path) -> None:
    if not web_root.is_dir():
        raise ViewerBundleError(f"Web root was not found: {web_root}")

    # Keep the exact source snapshot for provenance and copy the deployable
    # viewer paths to the bundle root so the ZIP opens as a static site.
    shutil.copytree(web_root, stage / "web")
    for name in ("viewer", "assets", "css", "js"):
        source = web_root / name
        if source.is_dir():
            shutil.copytree(source, stage / name)
    for name in ("theme.css",):
        source = web_root / name
        if source.is_file():
            shutil.copy2(source, stage / name)


def _iter_files(root: Path) -> Iterable[Path]:
    return (path for path in sorted(root.rglob("*")) if path.is_file())


def _write_manifest(stage: Path, pose_path: Path, web_root: Path) -> dict[str, Any]:
    files = []
    for path in _iter_files(stage):
        if path.name == "manifest.json":
            continue
        files.append({
            "path": path.relative_to(stage).as_posix(),
            "byte_size": path.stat().st_size,
            "sha256": _sha256(path),
        })
    manifest = {
        "schema_version": "viewer-bundle-1",
        "generated_at": datetime.now(UTC).isoformat(),
        "entrypoint": "index.html",
        "viewer_pose": "viewer_pose.json",
        "source": {
            "pose": pose_path.as_posix(),
            "web_root": web_root.as_posix(),
            "pose_sha256": _sha256(pose_path),
        },
        "files": files,
        "scientific_scope": (
            "Static visualization bundle for imported FlyGym rollout data. "
            "It does not run simulation or add biological interpretation."
        ),
    }
    (stage / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def build_bundle(
    pose_path: str | Path,
    *,
    output: str | Path = DEFAULT_OUTPUT,
    web_root: str | Path = DEFAULT_WEB_ROOT,
) -> tuple[Path, Path, dict[str, Any]]:
    """Build the unpacked bundle directory and its ZIP archive."""

    pose = Path(pose_path).expanduser().resolve()
    web = Path(web_root).expanduser().resolve()
    output_path = Path(output).expanduser().resolve()
    if not pose.is_file():
        raise ViewerBundleError(f"viewer_pose.json was not found: {pose}")
    document = _load_pose(pose)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stage = output_path.parent / output_path.stem
    if stage.resolve() == web.resolve() or stage.resolve() == pose.parent.resolve():
        raise ViewerBundleError("Bundle output must not overwrite the source web or dataset directory.")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)

    _copy_web_runtime(web, stage)
    (stage / "viewer_pose.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _copy_optional_source_metadata(pose, stage)
    _copy_local_mesh_asset(document, pose, stage, web)
    _write_entrypoint(stage)
    manifest = _write_manifest(stage, pose, web)

    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in _iter_files(stage):
            archive.write(path, Path("viewer_bundle") / path.relative_to(stage))
    return stage, output_path, manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose", type=Path, help="Path to viewer_pose.json. Auto-discovery is used when omitted.")
    parser.add_argument("--web-root", type=Path, default=DEFAULT_WEB_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        pose = find_viewer_pose(args.pose)
        stage, archive, manifest = build_bundle(pose, output=args.output, web_root=args.web_root)
    except ViewerBundleError as exc:
        print(f"Viewer bundle error: {exc}", file=sys.stderr)
        return 2
    print(f"Viewer bundle directory: {stage}")
    print(f"Viewer bundle archive: {archive}")
    print(f"Packaged files: {len(manifest['files'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
