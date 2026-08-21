from drosophila_pd.flystudio.asset_bundle import AssetBundle

def test_asset_bundle():
    bundle = AssetBundle(id="bundle1", asset_ids=["asset1", "asset2"])
    assert bundle.id == "bundle1"
    assert len(bundle.asset_ids) == 2
    assert bundle.compressed is True
