from drosophila_pd.flystudio.package_builder import PackageBuilder
from drosophila_pd.flystudio.project_package import ProjectPackage
from drosophila_pd.flystudio.metadata import ProjectMetadata

def test_package_builder():
    pkg = ProjectPackage(metadata=ProjectMetadata(name="B"))
    pkg.scene_data = {"a": 1}
    data = PackageBuilder.build(pkg)
    assert data.startswith(b'PK')
