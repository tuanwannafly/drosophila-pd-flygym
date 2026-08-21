from drosophila_pd.flystudio.asset_manifest import AssetManifest

def test_asset_manifest():
    manifest = AssetManifest(version="2.0", entries={"asset1": {"type": "mesh"}})
    json_str = manifest.serialize()

    manifest_deserialized = AssetManifest.deserialize(json_str)
    assert manifest_deserialized.version == "2.0"
    assert manifest_deserialized.entries["asset1"]["type"] == "mesh"
