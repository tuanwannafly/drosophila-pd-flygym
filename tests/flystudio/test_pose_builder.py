from drosophila_pd.flystudio.pose_builder import PoseBuilder
from drosophila_pd.flystudio.retarget_profile import RetargetProfile
from drosophila_pd.flystudio.retarget_mapping import RetargetMapping
from drosophila_pd.flystudio.playback_frame import PlaybackFrame

def test_pose_builder():
    rp = RetargetProfile(id="prof1")
    rp.mappings.append(RetargetMapping("ch1", "j1"))
    rp.mappings.append(RetargetMapping("ch2", "j2"))

    frame = PlaybackFrame(time=1.0, data={"ch1": (1.0, 2.0, 3.0), "ch2": 5.0})

    pose = PoseBuilder.build_from_frame(frame, rp)
    assert pose.id == "pose_1.0"
    assert "j1" in pose.joints
    assert "j2" in pose.joints
    assert pose.joints["j1"].transform.translation == (1.0, 2.0, 3.0)
    assert pose.joints["j2"].transform.translation == (0.0, 0.0, 0.0)
