from drosophila_pd.flystudio.statistics_panel import StatisticsPanel

def test_statistics_panel():
    panel = StatisticsPanel()
    panel.update(fps=60.0, frame_count=100)

    assert panel.fps == 60.0
    assert panel.frame_count == 100
