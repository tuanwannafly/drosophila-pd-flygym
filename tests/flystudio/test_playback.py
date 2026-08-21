import drosophila_pd.flystudio.playback as pb

def test_playback_exports():
    assert pb.PlaybackSession is not None
    assert pb.MotionPlayer is not None
    assert pb.TimelineController is not None
    assert pb.Interpolator is not None
    assert pb.PlaybackSerializer is not None
