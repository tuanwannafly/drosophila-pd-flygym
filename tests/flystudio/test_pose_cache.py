from drosophila_pd.flystudio.pose_cache import PoseCache
from drosophila_pd.flystudio.skeleton_pose import SkeletonPose

def test_pose_cache():
    cache = PoseCache(max_size=2)
    cache.put(0.0, SkeletonPose("p0"))
    cache.put(1.0, SkeletonPose("p1"))

    assert cache.get(0.0).id == "p0"

    cache.put(2.0, SkeletonPose("p2"))
    assert cache.get(0.0) is None
    assert cache.get(1.0).id == "p1"
