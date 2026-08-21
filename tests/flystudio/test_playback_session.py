from drosophila_pd.flystudio.playback_session import PlaybackSession

def test_playback_session():
    session = PlaybackSession(id="sess1", duration=5.0)
    assert session.id == "sess1"
    assert session.duration == 5.0
    assert session.player is not None
    assert session.player.timeline == session.timeline
