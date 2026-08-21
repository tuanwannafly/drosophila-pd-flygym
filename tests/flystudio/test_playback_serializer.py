from drosophila_pd.flystudio.playback_serializer import PlaybackSerializer
from drosophila_pd.flystudio.playback_session import PlaybackSession
from drosophila_pd.flystudio.timeline_controller import TimelineController

def test_playback_serializer():
    session = PlaybackSession(id="s1", duration=10.0)
    data = PlaybackSerializer.serialize(session)

    deserialized = PlaybackSerializer.deserialize(data)
    assert deserialized["session_id"] == "s1"
    assert deserialized["duration"] == 10.0
