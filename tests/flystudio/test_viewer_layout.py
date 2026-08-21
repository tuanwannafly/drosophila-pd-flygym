from drosophila_pd.flystudio.viewer_layout import ViewerLayout

def test_viewer_layout():
    layout = ViewerLayout(name="split", split_type="horizontal_split")
    assert layout.name == "split"
    assert layout.split_type == "horizontal_split"
    assert "main" in layout.viewport_ids
