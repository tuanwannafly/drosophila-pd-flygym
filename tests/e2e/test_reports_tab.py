from .conftest import assert_no_runtime_errors


def test_reports_and_publication_tabs_switch_without_errors(page):
    page.get_by_role("button", name="Reports").click()
    assert "Report center" in page.locator(".digital-laboratory-content").inner_text()
    page.get_by_role("button", name="Publication").click()
    assert "Publication center" in page.locator(".digital-laboratory-content").inner_text()
    page.get_by_role("button", name="Plugins").click()
    assert "Plugin manager" in page.locator(".digital-laboratory-content").inner_text()
    assert_no_runtime_errors(page)
