from drosophila_pd.flystudio.texture_asset import TextureAsset

def test_texture_asset():
    tex = TextureAsset(id="tex1", width=512, height=512)
    assert tex.id == "tex1"
    assert tex.width == 512
    assert tex.height == 512
    assert tex.format == "RGBA8"
