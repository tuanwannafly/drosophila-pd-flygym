from drosophila_pd.flystudio.timeline_controller import TimelineController

def test_timeline_controller():
    tl = TimelineController(duration=10.0)
    assert tl.current_time == 0.0

    tl.seek(5.0)
    assert tl.current_time == 5.0

    tl.seek(15.0)
    assert tl.current_time == 10.0

    tl.seek(-5.0)
    assert tl.current_time == 0.0
