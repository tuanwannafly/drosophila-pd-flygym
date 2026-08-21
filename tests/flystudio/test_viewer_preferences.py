from drosophila_pd.flystudio.viewer_preferences import ViewerPreferences

def test_viewer_preferences():
    prefs = ViewerPreferences(theme="light", ui_scale=1.5)
    assert prefs.theme == "light"
    assert prefs.ui_scale == 1.5
    assert prefs.auto_play is False
