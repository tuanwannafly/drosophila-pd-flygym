# Architecture

The playback engine consists of data containers and operational controllers.

- **Data Structures**: `PlaybackFrame`, `PlaybackClip`, and `PlaybackTrack` organize temporal data.
- **Timeline Control**: `TimelineController` serves as the source of truth for the current playback time.
- **Motion Player**: `MotionPlayer` reads delta-time (`dt`) updates, applies speed and looping logic, and advances the timeline.
- **Keyframes & Interpolation**: `KeyframeBuilder` converts raw arrays into structured clips, and `Interpolator` defines linear, step, and cubic blending.
- **Event Scheduling**: `FrameScheduler` and `EventTrack` map time values to callbacks or metadata markers.
- **Session & Caching**: `PlaybackSession` bundles a timeline, player, and statistics into one unit, while `PlaybackCache` caches pre-computed frames to avoid expensive recalculations.
- **Synchronization**: `SyncManager` aligns secondary timelines to a master timeline.
