from drosophila_pd.flystudio.recording_panel import RecordingPanel
from drosophila_pd.flystudio.viewer_state import ViewerState

def test_recording_panel():
    state = ViewerState()
    panel = RecordingPanel(state=state)

    panel.start_recording()
    assert state.recording_active is True

    panel.stop_recording()
    assert state.recording_active is False
