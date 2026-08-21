from drosophila_pd.flystudio.pose_interpolator import PoseInterpolator
from drosophila_pd.flystudio.skeleton_pose import SkeletonPose
from drosophila_pd.flystudio.joint_pose import JointPose
from drosophila_pd.flystudio.transform import Transform

def test_pose_interpolator():
    p1 = SkeletonPose(id="p1")
    p1.joints["j1"] = JointPose("j1", Transform(translation=(0.0, 0.0, 0.0)))
    p1.joints["j2"] = JointPose("j2", Transform(translation=(1.0, 1.0, 1.0)))

    p2 = SkeletonPose(id="p2")
    p2.joints["j1"] = JointPose("j1", Transform(translation=(10.0, 10.0, 10.0)))

    blended = PoseInterpolator.blend(p1, p2, 0.5)
    assert blended.id == "blended"
    assert blended.joints["j1"].transform.translation == (5.0, 5.0, 5.0)
    assert blended.joints["j2"].transform.translation == (1.0, 1.0, 1.0)
