from drosophila_pd.flystudio.package_validator import PackageValidator
from drosophila_pd.flystudio.project_package import ProjectPackage
from drosophila_pd.flystudio.metadata import ProjectMetadata

def test_package_validator():
    pkg = ProjectPackage(metadata=ProjectMetadata(name=""))
    errors = PackageValidator.validate(pkg)
    assert "Missing project name" in errors
    assert "Package contains no active data payload" in errors
