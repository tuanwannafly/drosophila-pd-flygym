from drosophila_pd.flystudio.skeleton_pose import SkeletonPose
from drosophila_pd.flystudio.joint_pose import JointPose

def test_skeleton_pose():
    sk = SkeletonPose(id="sk1")
    sk.joints["j1"] = JointPose(id="j1")
    assert sk.id == "sk1"
    assert "j1" in sk.joints
