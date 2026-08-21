from drosophila_pd.flystudio.pose_serializer import PoseSerializer
from drosophila_pd.flystudio.skeleton_pose import SkeletonPose
from drosophila_pd.flystudio.joint_pose import JointPose

def test_pose_serializer():
    pose = SkeletonPose(id="sk1")
    pose.joints["j1"] = JointPose("j1")

    data = PoseSerializer.serialize(pose)
    deserialized = PoseSerializer.deserialize(data)

    assert deserialized["id"] == "sk1"
    assert deserialized["joint_count"] == 1
