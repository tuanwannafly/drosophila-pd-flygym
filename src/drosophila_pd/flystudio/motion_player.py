from dataclasses import dataclass
from .timeline_controller import TimelineController

@dataclass
class MotionPlayer:
    """Plays motion data on the timeline."""
    timeline: TimelineController
    speed: float = 1.0
    is_playing: bool = False
    loop: bool = False
    is_reverse: bool = False

    def play(self):
        self.is_playing = True

    def pause(self):
        self.is_playing = False

    def step(self, dt: float):
        if not self.is_playing:
            return

        delta = dt * self.speed
        if self.is_reverse:
            delta = -delta

        new_time = self.timeline.current_time + delta
        if new_time > self.timeline.duration:
            new_time = 0.0 if self.loop else self.timeline.duration
            if not self.loop:
                self.pause()
        elif new_time < 0:
            new_time = self.timeline.duration if self.loop else 0.0
            if not self.loop:
                self.pause()

        self.timeline.seek(new_time)
