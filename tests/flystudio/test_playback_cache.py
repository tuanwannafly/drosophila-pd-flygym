from drosophila_pd.flystudio.playback_cache import PlaybackCache

def test_playback_cache():
    cache = PlaybackCache(max_frames=2)
    cache.store_frame(0.0, "frame0")
    cache.store_frame(1.0, "frame1")
    assert cache.get_frame(0.0) == "frame0"

    cache.store_frame(2.0, "frame2")
    assert cache.get_frame(0.0) is None
    assert cache.get_frame(1.0) == "frame1"
    assert cache.get_frame(2.0) == "frame2"
