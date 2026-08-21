from drosophila_pd.flystudio.sync_manager import SyncManager
from drosophila_pd.flystudio.timeline_controller import TimelineController

def test_sync_manager():
    master = TimelineController(duration=10.0)
    master.seek(4.5)

    slave = TimelineController(duration=20.0)
    sync = SyncManager(master=master)

    sync.sync(slave)
    assert slave.current_time == 4.5
