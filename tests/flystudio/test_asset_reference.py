from drosophila_pd.flystudio.asset_reference import AssetReference

def test_asset_reference():
    ref = AssetReference(id="test1", relative_path="path/to/asset.png")
    assert ref.id == "test1"
    assert ref.relative_path == "path/to/asset.png"
    assert ref.resolved_path is None
