from drosophila_pd.flystudio.project_package import ProjectPackage
from drosophila_pd.flystudio.metadata import ProjectMetadata

def test_project_package():
    pkg = ProjectPackage(metadata=ProjectMetadata(name="P"))
    pkg.assets["a"] = b"123"
    assert pkg.metadata.name == "P"
    assert len(pkg.assets) == 1
