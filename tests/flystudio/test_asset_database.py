from drosophila_pd.flystudio.asset_database import AssetDatabase

def test_asset_database():
    db = AssetDatabase()
    db.register_asset(uuid="test1", asset={"data": 1}, asset_tags=["tag1"])
    assert db.get_asset("test1") == {"data": 1}
    assert "tag1" in db.tags["test1"]
