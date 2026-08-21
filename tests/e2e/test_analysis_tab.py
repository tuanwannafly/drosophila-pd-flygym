from .conftest import assert_no_runtime_errors


def test_analysis_tab_has_explicit_data_state(page):
    page.get_by_role("button", name="Analysis").click()
    assert "Analysis" in page.locator(".digital-laboratory-content").inner_text()
    assert_no_runtime_errors(page)
