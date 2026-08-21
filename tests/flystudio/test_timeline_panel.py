from drosophila_pd.flystudio.timeline_panel import TimelinePanel
from drosophila_pd.flystudio.viewer_state import ViewerState

def test_timeline_panel():
    state = ViewerState()
    panel = TimelinePanel(state=state)

    panel.seek(5.5)
    assert state.current_time == 5.5
