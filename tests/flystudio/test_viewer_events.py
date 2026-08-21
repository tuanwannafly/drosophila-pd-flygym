from drosophila_pd.flystudio.viewer_events import ViewerEvents

def test_viewer_events():
    events = ViewerEvents()
    called = []

    def on_event(name, payload):
        called.append((name, payload))

    events.subscribe(on_event)
    events.dispatch("click", {"x": 10})

    assert len(called) == 1
    assert called[0] == ("click", {"x": 10})
