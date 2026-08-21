from drosophila_pd.flystudio.motion_player import MotionPlayer
from drosophila_pd.flystudio.timeline_controller import TimelineController

def test_motion_player():
    tl = TimelineController(duration=10.0)
    player = MotionPlayer(timeline=tl)

    player.step(1.0)
    assert tl.current_time == 0.0

    player.play()
    player.step(1.0)
    assert tl.current_time == 1.0

    player.pause()
    player.step(1.0)
    assert tl.current_time == 1.0

    player.play()
    player.speed = 2.0
    player.step(1.0)
    assert tl.current_time == 3.0

    player.is_reverse = True
    player.step(1.0)
    assert tl.current_time == 1.0

    player.is_reverse = False
    player.step(10.0)
    assert tl.current_time == 10.0
    assert not player.is_playing

    player.loop = True
    player.play()
    player.step(1.0)
    assert tl.current_time == 0.0

    player.is_reverse = True
    player.step(1.0)
    assert tl.current_time == 10.0
