from drosophila_pd.flystudio.selection_panel import SelectionPanel

def test_selection_panel():
    panel = SelectionPanel()
    panel.select("item1")
    panel.select("item2")
    panel.select("item1")

    assert len(panel.selected_items) == 2

    panel.clear()
    assert len(panel.selected_items) == 0
