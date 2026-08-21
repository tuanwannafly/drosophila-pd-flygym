"""Playwright fixtures for browser runtime checks.

Viewer pose tests require a real imported artifact supplied by
``FLY_STUDIO_VIEWER_POSE``. No scientific fixture is generated here.
"""

from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import time

import pytest

playwright_api = pytest.importorskip("playwright.sync_api", reason="Install the optional e2e dependency and Chromium to run browser tests.")
from playwright.sync_api import Browser, Page, Playwright, sync_playwright  # noqa: E402


ROOT = Path(__file__).parents[2]
SCREENSHOT_DIR = ROOT / "docs" / "runtime" / "screenshots"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-e2e",
        action="store_true",
        default=False,
        help="Run browser E2E tests; omitted from the default Python suite.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-e2e"):
        return
    skip = pytest.mark.skip(reason="Browser E2E tests require the explicit --run-e2e flag.")
    for item in items:
        if "tests\\e2e" in str(item.fspath) or "tests/e2e" in str(item.fspath):
            item.add_marker(skip)


@pytest.fixture(scope="session")
def web_server(tmp_path_factory: pytest.TempPathFactory):
    ready_file = tmp_path_factory.mktemp("web-server") / "ready.txt"
    process = subprocess.Popen(
        [sys.executable, "scripts/run_web_demo.py", "--port", "0", "--quiet", "--ready-file", str(ready_file)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and not ready_file.exists():
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"Web demo server exited: {output}")
        time.sleep(0.05)
    if not ready_file.exists():
        process.terminate()
        raise RuntimeError("Web demo server did not publish a ready URL.")
    try:
        yield ready_file.read_text(encoding="utf-8").strip()
    finally:
        process.terminate()
        process.wait(timeout=10)


@pytest.fixture(scope="session")
def playwright() -> Playwright:
    with sync_playwright() as instance:
        yield instance


@pytest.fixture(scope="session")
def browser(playwright: Playwright) -> Browser:
    instance = playwright.chromium.launch(headless=True, args=["--disable-gpu"])
    try:
        yield instance
    finally:
        instance.close()


@pytest.fixture
def page(browser: Browser, request: pytest.FixtureRequest, web_server: str) -> Page:
    current = browser.new_page()
    runtime_errors: list[str] = []
    current.on("pageerror", lambda error: runtime_errors.append(f"pageerror: {error}"))
    current.on("console", lambda message: runtime_errors.append(f"console.error: {message.text}") if message.type == "error" else None)
    current.goto(web_server, wait_until="networkidle")
    current.wait_for_selector(".digital-laboratory-dashboard")
    current._flystudio_runtime_errors = runtime_errors  # type: ignore[attr-defined]
    yield current
    screenshot_name = request.node.name.replace("::", "-") + ".png"
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    current.screenshot(path=str(SCREENSHOT_DIR / screenshot_name), full_page=True)
    current.close()


def assert_no_runtime_errors(page: Page) -> None:
    errors = getattr(page, "_flystudio_runtime_errors", [])
    assert not errors, "Browser runtime errors:\n" + "\n".join(errors)


def real_pose_path() -> Path:
    value = os.environ.get("FLY_STUDIO_VIEWER_POSE")
    if not value:
        pytest.skip("Set FLY_STUDIO_VIEWER_POSE to a real viewer_pose.json artifact.")
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        pytest.skip(f"Real viewer pose artifact not found: {path}")
    return path


def load_real_pose(page: Page) -> Path:
    path = real_pose_path()
    page.locator("#load-json-input").set_input_files(str(path))
    page.locator(".three-viewer-shell").wait_for(state="visible")
    return path
