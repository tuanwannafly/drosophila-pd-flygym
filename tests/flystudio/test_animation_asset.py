from drosophila_pd.flystudio.animation_asset import AnimationAsset

def test_animation_asset():
    anim = AnimationAsset(id="anim1", duration=2.5)
    assert anim.id == "anim1"
    assert anim.duration == 2.5
    anim.events[1.0] = "foot_strike"
    assert anim.events[1.0] == "foot_strike"
