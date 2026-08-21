from drosophila_pd.flystudio.material_asset import MaterialAsset

def test_material_asset():
    mat = MaterialAsset(id="mat1", roughness=0.8)
    assert mat.id == "mat1"
    assert mat.roughness == 0.8
    assert mat.albedo_texture_id is None
