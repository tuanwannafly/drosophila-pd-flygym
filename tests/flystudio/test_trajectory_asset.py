from drosophila_pd.flystudio.trajectory_asset import TrajectoryAsset

def test_trajectory_asset():
    traj = TrajectoryAsset(id="traj1", frame_count=300)
    assert traj.id == "traj1"
    assert traj.frame_count == 300
    assert traj.frame_rate == 30.0
