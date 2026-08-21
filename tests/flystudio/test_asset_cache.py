from drosophila_pd.flystudio.asset_cache import AssetCache

def test_asset_cache():
    cache = AssetCache(max_memory_mb=2.0)
    cache.put("asset1", "data1", size_mb=1.0)
    assert cache.get("asset1") == "data1"

    cache.put("asset2", "data2", size_mb=1.0)
    assert cache.get("asset1") == "data1"

    cache.put("asset3", "data3", size_mb=1.0)
    assert cache.get("asset2") is None
    assert cache.get("asset1") == "data1"
    assert cache.get("asset3") == "data3"
