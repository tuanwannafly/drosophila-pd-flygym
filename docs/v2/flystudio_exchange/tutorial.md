# Tutorial

```python
from drosophila_pd.flystudio.exchange import ProjectPackage, ProjectMetadata, PackageBuilder, PackageLoader

# Create a package
pkg = ProjectPackage(metadata=ProjectMetadata(name="My Session"))
pkg.scene_data = {"nodes": []}
pkg.assets["model.obj"] = b"mesh data..."

# Build ZIP
data = PackageBuilder.build(pkg)
with open("session.flystudio", "wb") as f:
    f.write(data)

# Load ZIP
with open("session.flystudio", "rb") as f:
    loaded = PackageLoader.load(f.read())
print(loaded.metadata.name)
```
