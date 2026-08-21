from drosophila_pd.flystudio.viewer_state import ViewerState

def test_viewer_state():
    state = ViewerState()
    assert state.is_playing is False
    assert state.current_time == 0.0
    assert state.show_skeleton is True
    assert state.show_grid is True
