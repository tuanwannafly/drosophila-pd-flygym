from drosophila_pd.flystudio.playback_panel import PlaybackPanel
from drosophila_pd.flystudio.viewer_state import ViewerState

def test_playback_panel():
    state = ViewerState()
    panel = PlaybackPanel(state=state)

    panel.play()
    assert state.is_playing is True

    panel.pause()
    assert state.is_playing is False
