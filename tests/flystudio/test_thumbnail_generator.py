from drosophila_pd.flystudio.thumbnail_generator import ThumbnailGenerator

def test_thumbnail_generator():
    data = ThumbnailGenerator.generate_placeholder()
    assert data.startswith(b'\x89PNG')
