from drosophila_pd.flystudio.viewport_controller import ViewportController
from drosophila_pd.flystudio.viewer_state import ViewerState

def test_viewport_controller():
    state = ViewerState()
    ctrl = ViewportController(id="vp1", state=state)

    assert state.show_skeleton is True
    ctrl.toggle_skeleton()
    assert state.show_skeleton is False

    assert state.show_grid is True
    ctrl.toggle_grid()
    assert state.show_grid is False
