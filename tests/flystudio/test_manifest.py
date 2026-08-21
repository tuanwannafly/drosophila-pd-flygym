from drosophila_pd.flystudio.manifest import Manifest

def test_manifest():
    m = Manifest()
    m.add_entry("test.txt", b"hello")
    assert len(m.entries) == 1
    assert m.entries[0].path == "test.txt"
    assert m.entries[0].size_bytes == 5
