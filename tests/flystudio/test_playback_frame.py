from drosophila_pd.flystudio.playback_frame import PlaybackFrame

def test_playback_frame():
    frame = PlaybackFrame(time=1.5, data={"pos": [0, 1, 0]})
    assert frame.time == 1.5
    assert frame.data["pos"] == [0, 1, 0]
