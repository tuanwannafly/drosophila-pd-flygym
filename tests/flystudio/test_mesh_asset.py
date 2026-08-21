from drosophila_pd.flystudio.mesh_asset import MeshAsset

def test_mesh_asset():
    mesh = MeshAsset(id="mesh1", vertices_count=100)
    assert mesh.id == "mesh1"
    assert mesh.vertices_count == 100
    assert mesh.has_tangents is False
