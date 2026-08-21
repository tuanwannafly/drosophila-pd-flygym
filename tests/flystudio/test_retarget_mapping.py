from drosophila_pd.flystudio.retarget_mapping import RetargetMapping

def test_retarget_mapping():
    rm = RetargetMapping(source_channel="ch1", target_joint_id="j1")
    assert rm.source_channel == "ch1"
    assert rm.target_joint_id == "j1"
    assert rm.weight == 1.0
