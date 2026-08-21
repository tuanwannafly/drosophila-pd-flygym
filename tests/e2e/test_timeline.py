from .conftest import assert_no_runtime_errors, load_real_pose


def test_timeline_seek_updates_shared_frame(page):
    load_real_pose(page)
    slider = page.locator("#timeline .timeline-slider")
    if slider.get_attribute("max") == "0":
        page.locator(".three-viewer-timeline [data-role=frame]").fill("0")
        assert page.locator("#timeline .timeline-current-frame").inner_text().startswith("Current Frame: 0")
    else:
        slider.fill("1")
        assert page.locator("#timeline .timeline-current-frame").inner_text().startswith("Current Frame: 1")
    assert_no_runtime_errors(page)
