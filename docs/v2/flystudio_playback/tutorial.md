# Tutorial

```python
from drosophila_pd.flystudio.playback import TimelineController, MotionPlayer

# Setup a timeline of 10 seconds
timeline = TimelineController(duration=10.0)

# Create a player
player = MotionPlayer(timeline=timeline, loop=True, speed=2.0)

# Play the animation
player.play()

# Advance by 1 real-time second (advances timeline by 2 seconds due to speed)
player.step(1.0)

print(f"Current Time: {timeline.current_time}")  # 2.0
```
