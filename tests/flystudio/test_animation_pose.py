from drosophila_pd.flystudio.animation_pose import AnimationPose
from drosophila_pd.flystudio.skeleton_pose import SkeletonPose

def test_animation_pose():
    base = SkeletonPose(id="base")
    anim = AnimationPose(base_pose=base)
    assert anim.base_pose.id == "base"
    assert len(anim.layers) == 0
