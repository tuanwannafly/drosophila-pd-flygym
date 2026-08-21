from drosophila_pd.flystudio.playback_statistics import PlaybackStatistics

def test_playback_statistics():
    stats = PlaybackStatistics(frames_played=100, dropped_frames=2, total_time=3.5)
    report = stats.generate_report()
    assert "Played: 100" in report
    assert "Dropped: 2" in report
    assert "Time: 3.5s" in report
