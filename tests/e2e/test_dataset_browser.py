from .conftest import assert_no_runtime_errors


def test_dataset_browser_is_available(page):
    page.get_by_role("button", name="Datasets").click()
    assert page.get_by_role("button", name="Load dataset JSON").is_visible()
    assert "No experiments loaded" in page.locator("#experiment-manager").inner_text()
    assert_no_runtime_errors(page)
