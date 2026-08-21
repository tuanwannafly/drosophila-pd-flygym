from .conftest import assert_no_runtime_errors


def test_app_loads_without_browser_runtime_errors(page):
    assert page.title() == "Fly Studio Web Platform"
    assert page.locator(".digital-laboratory-tabs button").count() == 8
    page.screenshot(path="docs/runtime/screenshots/app-load.png", full_page=True)
    assert_no_runtime_errors(page)
