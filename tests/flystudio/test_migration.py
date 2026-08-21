from drosophila_pd.flystudio.migration import Migration
from drosophila_pd.flystudio.project_package import ProjectPackage
from drosophila_pd.flystudio.metadata import ProjectMetadata
from drosophila_pd.flystudio.versioning import Version

def test_migration():
    pkg = ProjectPackage(metadata=ProjectMetadata(name="M", version=Version(1, 0, 0)))
    Migration.migrate(pkg)
    assert pkg.metadata.custom_data.get("migrated_from_v1") is True
