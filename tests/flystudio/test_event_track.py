from drosophila_pd.flystudio.event_track import EventTrack

def test_event_track():
    track = EventTrack(id="events")
    track.add_event(1.5, "jump")
    track.add_bookmark(2.0, "start_running")

    assert track.events[1.5] == "jump"
    assert track.bookmarks[2.0] == "start_running"
