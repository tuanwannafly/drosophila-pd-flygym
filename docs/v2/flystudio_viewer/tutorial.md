# Tutorial

```python
from drosophila_pd.flystudio.viewer import ViewerSession, PlaybackPanel

# Create a master session
session = ViewerSession(id="viewer_1")

# Create a playback panel pointing to the session state
playback = PlaybackPanel(state=session.state)

# Trigger playback
playback.play()
print(session.state.is_playing) # True
```
