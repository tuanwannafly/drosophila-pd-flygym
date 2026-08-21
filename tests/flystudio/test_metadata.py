from drosophila_pd.flystudio.metadata import ProjectMetadata
from drosophila_pd.flystudio.versioning import Version

def test_metadata():
    m = ProjectMetadata(name="Test")
    assert m.name == "Test"
    assert m.author == "Unknown"
    assert str(m.version) == "1.0.0"
