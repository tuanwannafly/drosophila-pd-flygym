import json
from drosophila_pd.flystudio.project_package import ProjectPackage
from drosophila_pd.flystudio.metadata import ProjectMetadata
from drosophila_pd.flystudio.package_serializer import PackageSerializer

def test_package_serializer():
    pkg = ProjectPackage(metadata=ProjectMetadata(name="S"))
    pkg.manifest.add_entry("a", b"a")

    meta_str = PackageSerializer.serialize_metadata(pkg)
    assert json.loads(meta_str)["name"] == "S"

    mani_str = PackageSerializer.serialize_manifest(pkg)
    assert len(json.loads(mani_str)["entries"]) == 1
