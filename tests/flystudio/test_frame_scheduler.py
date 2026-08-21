from drosophila_pd.flystudio.frame_scheduler import FrameScheduler

def test_frame_scheduler():
    called = []
    def cb(idx): called.append(idx)

    scheduler = FrameScheduler(callbacks=[cb])
    scheduler.execute_frame(42)
    assert called == [42]
