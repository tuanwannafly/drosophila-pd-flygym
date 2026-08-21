# Tutorial

```python
from drosophila_pd.flystudio.asset_database import AssetDatabase
from drosophila_pd.flystudio.mesh_asset import MeshAsset

db = AssetDatabase()
mesh = MeshAsset(id="fly_leg", vertices_count=5000, normals_count=5000)

db.register_asset("fly_leg", mesh, asset_tags=["anatomy", "leg"])

retrieved = db.get_asset("fly_leg")
print(retrieved.vertices_count)
```
