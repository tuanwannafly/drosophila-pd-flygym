# API Reference

- `PlaybackFrame`: Container for timestamped data.
- `PlaybackClip`: Sequence of frames.
- `PlaybackTrack`: Named channel containing clips.
- `TimelineController`: Absolute time tracker.
- `Interpolator`: Static math functions for blending.
- `KeyframeBuilder`: Builder utility for raw data arrays.
- `MotionPlayer`: Delta-time player (play, pause, step, seek, speed).
- `FrameScheduler`: Callback scheduler per frame.
- `EventTrack`: Bookmarks and event annotations.
- `PlaybackSerializer`: JSON import/export.
- `PlaybackStatistics`: Dropped frame and time metrics.
- `PlaybackSession`: Master container.
- `PlaybackCache`: Memory cache for decoded frames.
- `SyncManager`: Master/slave timeline linking.
