from drosophila_pd.flystudio.resource_manager import ResourceManager
from drosophila_pd.flystudio.asset_database import AssetDatabase
from drosophila_pd.flystudio.asset_loader import AssetLoader
from drosophila_pd.flystudio.asset_cache import AssetCache

def test_resource_manager():
    db = AssetDatabase()
    db.register_asset("res1", {"data": "test"})
    loader = AssetLoader(cache=AssetCache())
    rm = ResourceManager(database=db, loader=loader)

    assert rm.get_resource("res1") == {"data": "test"}
    assert rm.get_resource("unknown") is None
