from drosophila_pd.flystudio.pose_statistics import PoseStatistics

def test_pose_statistics():
    stats = PoseStatistics(poses_generated=5, cache_hits=2, validation_errors=1)
    report = stats.report()
    assert "Poses: 5" in report
    assert "Hits: 2" in report
    assert "Errors: 1" in report
