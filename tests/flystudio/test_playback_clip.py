from drosophila_pd.flystudio.playback_clip import PlaybackClip
from drosophila_pd.flystudio.playback_frame import PlaybackFrame

def test_playback_clip():
    f1 = PlaybackFrame(time=0.0, data={})
    f2 = PlaybackFrame(time=1.0, data={})
    clip = PlaybackClip(id="clip1", frames=[f1, f2], duration=1.0)
    assert clip.id == "clip1"
    assert len(clip.frames) == 2
    assert clip.duration == 1.0
