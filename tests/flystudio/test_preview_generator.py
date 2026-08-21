from drosophila_pd.flystudio.preview_generator import PreviewGenerator
from drosophila_pd.flystudio.project_package import ProjectPackage
from drosophila_pd.flystudio.metadata import ProjectMetadata

def test_preview_generator():
    pkg = ProjectPackage(metadata=ProjectMetadata(name="P"))
    PreviewGenerator.generate(pkg)
    assert pkg.preview_image is not None
