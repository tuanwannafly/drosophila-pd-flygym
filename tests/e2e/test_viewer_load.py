from .conftest import assert_no_runtime_errors, load_real_pose


def test_real_viewer_pose_loads(page):
    load_real_pose(page)
    assert page.locator(".three-viewer-canvas").is_visible()
    assert page.locator(".three-viewer-timeline").is_visible()
    timeline = page.locator(".three-viewer-timeline")
    assert "Frame 0" in timeline.inner_text()
    assert "FPS" in timeline.inner_text()
    assert "Time" in timeline.inner_text()
    assert timeline.locator('[data-role="camera"]').is_visible()
    assert timeline.locator('[data-role="shadow"]').is_checked()
    assert_no_runtime_errors(page)
