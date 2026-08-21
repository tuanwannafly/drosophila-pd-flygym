from .conftest import assert_no_runtime_errors, load_real_pose


def test_viewer_playback_controls(page):
    load_real_pose(page)
    controls = page.locator(".three-viewer-timeline")
    controls.locator('[data-action="play"]').click()
    controls.locator('[data-action="pause"]').click()
    controls.locator('[data-action="stop"]').click()
    controls.locator('[data-role="loop"]').check()
    controls.locator('[data-role="speed"]').select_option("2")
    assert controls.locator('[data-role="loop"]').is_checked()
    assert controls.locator('[data-role="speed"]').input_value() == "2"
    assert_no_runtime_errors(page)
