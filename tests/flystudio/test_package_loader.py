from drosophila_pd.flystudio.package_builder import PackageBuilder
from drosophila_pd.flystudio.package_loader import PackageLoader
from drosophila_pd.flystudio.project_package import ProjectPackage
from drosophila_pd.flystudio.metadata import ProjectMetadata

def test_package_loader():
    pkg = ProjectPackage(metadata=ProjectMetadata(name="L"))
    pkg.scene_data = {"nodes": []}
    pkg.assets["f.txt"] = b"123"

    data = PackageBuilder.build(pkg)

    loaded = PackageLoader.load(data)
    assert loaded.metadata.name == "L"
    assert loaded.scene_data == {"nodes": []}
    assert loaded.preview_image is not None
