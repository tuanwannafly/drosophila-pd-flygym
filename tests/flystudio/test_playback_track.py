from drosophila_pd.flystudio.playback_track import PlaybackTrack
from drosophila_pd.flystudio.playback_clip import PlaybackClip

def test_playback_track():
    clip = PlaybackClip(id="c1")
    track = PlaybackTrack(id="t1", clips=[clip])
    assert track.id == "t1"
    assert len(track.clips) == 1
    assert track.clips[0].id == "c1"
