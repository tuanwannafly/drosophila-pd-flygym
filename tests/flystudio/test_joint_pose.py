from drosophila_pd.flystudio.joint_pose import JointPose

def test_joint_pose():
    jp = JointPose(id="j1")
    assert jp.id == "j1"
    assert jp.transform.translation == (0.0, 0.0, 0.0)
