from drosophila_pd.flystudio.keyframe_builder import KeyframeBuilder

def test_keyframe_builder():
    times = [0.0, 1.0, 2.0]
    data = [{"v": 1}, {"v": 2}, {"v": 3}]
    clip = KeyframeBuilder.build_clip("c1", times, data)

    assert clip.id == "c1"
    assert clip.duration == 2.0
    assert len(clip.frames) == 3
    assert clip.frames[1].time == 1.0
    assert clip.frames[1].data["v"] == 2
