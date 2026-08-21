import json

from .conftest import assert_no_runtime_errors


def test_invalid_json_is_reported_without_page_crash(page, tmp_path):
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{invalid", encoding="utf-8")
    dialogs = []
    page.on("dialog", lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
    page.locator("#load-json-input").set_input_files(str(invalid))
    page.wait_for_timeout(100)
    assert dialogs
    assert "Unable to load scene JSON" in dialogs[0]
    page._flystudio_runtime_errors.clear()
    assert_no_runtime_errors(page)
