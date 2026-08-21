"""Serve a viewer bundle or the repository web viewer with a pose artifact."""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import sys
import tempfile
from urllib.parse import unquote, urlsplit
import webbrowser

from build_viewer_bundle import _copy_web_runtime, _write_entrypoint
from drosophila_pd.viewer_export.discovery import find_latest_viewer_pose


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEB_ROOT = REPOSITORY_ROOT / "web"


def find_viewer_pose(path: str | Path | None = None, *, repo_root: Path = REPOSITORY_ROOT) -> Path:
    """Find a pose file without modifying the source tree."""

    if path is not None:
        candidate = Path(path).expanduser().resolve()
        if not candidate.is_file():
            raise FileNotFoundError(f"viewer_pose.json was not found: {candidate}")
        return candidate

    pose = find_latest_viewer_pose(repo_root)
    if pose is None:
        raise FileNotFoundError("No viewer_pose.json found. Pass --pose PATH.")
    return pose


def resolve_web_root(path: str | Path | None = None) -> Path:
    """Resolve a bundle directory or the repository's source web directory."""

    if path is not None:
        root = Path(path).expanduser().resolve()
    elif (Path.cwd() / "index.html").is_file() and (Path.cwd() / "viewer").is_dir():
        root = Path.cwd().resolve()
    else:
        root = DEFAULT_WEB_ROOT.resolve()
    if not (root / "index.html").is_file():
        raise FileNotFoundError(f"Viewer index.html was not found under {root}")
    return root


class _PoseHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, pose_path: Path, **kwargs):
        self.pose_path = pose_path
        super().__init__(*args, **kwargs)

    def translate_path(self, request_path: str) -> str:
        path = unquote(urlsplit(request_path).path).rstrip("/")
        if path == "/viewer_pose.json":
            return str(self.pose_path)
        return super().translate_path(request_path)

    def log_message(self, format: str, *args: object) -> None:
        if not getattr(self.server, "quiet", False):
            super().log_message(format, *args)


@contextmanager
def _runtime_root(root: Path, pose: Path):
    """Yield an auto-loading root without modifying the source ``web/`` tree."""

    is_bundle = (root / "web").is_dir() and (root / "viewer").is_dir()
    if is_bundle:
        yield root
        return

    with tempfile.TemporaryDirectory(prefix="fly-studio-viewer-") as temporary:
        runtime = Path(temporary)
        _copy_web_runtime(root, runtime)
        shutil.copy2(pose, runtime / "viewer_pose.json")
        _write_entrypoint(runtime)
        yield runtime


def serve(
    web_root: str | Path,
    pose_path: str | Path,
    *,
    host: str = "127.0.0.1",
    port: int = 0,
    open_browser: bool = True,
    quiet: bool = False,
    ready_file: str | Path | None = None,
) -> None:
    """Serve static viewer files and map ``/viewer_pose.json`` to the pose."""

    root = Path(web_root).resolve()
    pose = Path(pose_path).resolve()
    with _runtime_root(root, pose) as runtime:
        handler = partial(_PoseHandler, directory=str(runtime), pose_path=pose)
        with ThreadingHTTPServer((host, port), handler) as server:
            server.quiet = quiet
            bound_host = "127.0.0.1" if host in {"0.0.0.0", "::"} else host
            url = f"http://{bound_host}:{server.server_address[1]}/index.html"
            print(f"Fly Studio Viewer: {url}", flush=True)
            print("Press Ctrl+C to stop the server.", flush=True)
            if ready_file is not None:
                target = Path(ready_file).expanduser().resolve()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(url + "\n", encoding="utf-8")
            if open_browser:
                webbrowser.open(url)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("\nFly Studio Viewer stopped.", flush=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pose", type=Path, help="Path to viewer_pose.json. Auto-discovery is used when omitted.")
    parser.add_argument("--root", type=Path, help="Unpacked viewer bundle directory or alternate web root.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="Port, or 0 to select a free port.")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the default browser.")
    parser.add_argument("--quiet", action="store_true", help="Suppress HTTP request logs.")
    parser.add_argument("--ready-file", type=Path, help="Write the URL after the server is ready.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        root = resolve_web_root(args.root)
        pose = find_viewer_pose(args.pose)
        serve(
            root,
            pose,
            host=args.host,
            port=args.port,
            open_browser=not args.no_browser,
            quiet=args.quiet,
            ready_file=args.ready_file,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Viewer server error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
