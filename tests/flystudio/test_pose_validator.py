from drosophila_pd.flystudio.pose_validator import PoseValidator
from drosophila_pd.flystudio.retarget_profile import RetargetProfile
from drosophila_pd.flystudio.retarget_mapping import RetargetMapping
from drosophila_pd.flystudio.skeleton_pose import SkeletonPose
from drosophila_pd.flystudio.joint_pose import JointPose

def test_pose_validator():
    rp = RetargetProfile(id="prof")
    rp.mappings.append(RetargetMapping("ch1", "j1"))
    rp.mappings.append(RetargetMapping("ch2", "j2"))

    validator = PoseValidator(profile=rp)

    pose = SkeletonPose("p1")
    pose.joints["j1"] = JointPose("j1")

    errors = validator.validate(pose)
    assert len(errors) == 1
    assert "Missing joint: j2" in errors
