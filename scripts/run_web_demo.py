"""Serve the static Fly Studio Web application without a Node dependency."""

from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        if not getattr(self.server, "quiet", False):
            super().log_message(format, *args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--open", action="store_true", dest="open_browser", help="Open the URL in the default browser.")
    parser.add_argument("--quiet", action="store_true", help="Suppress request logs.")
    parser.add_argument("--ready-file", type=Path, help="Write the serving URL here after startup.")
    return parser


def serve(host: str = "127.0.0.1", port: int = 8000, *, open_browser: bool = False, quiet: bool = False, ready_file: Path | None = None) -> None:
    web_root = Path(__file__).resolve().parents[1] / "web"
    handler = partial(QuietHandler, directory=str(web_root))
    with ThreadingHTTPServer((host, port), handler) as server:
        server.quiet = quiet
        address = server.server_address
        url = f"http://{address[0]}:{address[1]}/index.html"
        print(f"Fly Studio Web demo: {url}", flush=True)
        print("Open this URL in a browser. Press Ctrl+C to stop the server.", flush=True)
        if ready_file:
            ready_file.parent.mkdir(parents=True, exist_ok=True)
            ready_file.write_text(url + "\n", encoding="utf-8")
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nFly Studio Web demo stopped.", flush=True)


def main() -> None:
    args = build_parser().parse_args()
    serve(args.host, args.port, open_browser=args.open_browser, quiet=args.quiet, ready_file=args.ready_file)


if __name__ == "__main__":
    main()
