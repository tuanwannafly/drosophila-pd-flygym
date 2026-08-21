from drosophila_pd.flystudio.retarget_profile import RetargetProfile
from drosophila_pd.flystudio.retarget_mapping import RetargetMapping

def test_retarget_profile():
    rm = RetargetMapping(source_channel="ch1", target_joint_id="j1")
    rp = RetargetProfile(id="prof1", mappings=[rm])
    assert rp.id == "prof1"
    assert rp.mappings[0].source_channel == "ch1"
