import drosophila_pd.flystudio.viewer as viewer

def test_viewer_exports():
    assert viewer.ViewerState is not None
    assert viewer.ViewerLayout is not None
    assert viewer.ViewportController is not None
    assert viewer.TimelinePanel is not None
    assert viewer.CameraPanel is not None
    assert viewer.CameraPreset is not None
    assert viewer.PlaybackPanel is not None
    assert viewer.SelectionPanel is not None
    assert viewer.StatisticsPanel is not None
    assert viewer.RecordingPanel is not None
    assert viewer.ViewerPreferences is not None
    assert viewer.ViewerEvents is not None
    assert viewer.ProjectWorkspace is not None
    assert viewer.ViewerSession is not None
    assert viewer.ViewerSerializer is not None
