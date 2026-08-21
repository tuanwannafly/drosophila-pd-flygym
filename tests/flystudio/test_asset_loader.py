from drosophila_pd.flystudio.asset_loader import AssetLoader
from drosophila_pd.flystudio.asset_cache import AssetCache
from drosophila_pd.flystudio.asset_reference import AssetReference

def test_asset_loader():
    cache = AssetCache()
    loader = AssetLoader(cache=cache)
    ref = AssetReference(id="asset1")

    loaded = loader.load(ref)
    assert loaded == {"data": "dummy"}
    assert cache.get("asset1") == loaded
