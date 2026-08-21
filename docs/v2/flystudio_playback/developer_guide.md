# Developer Guide

When extending the Playback engine:
- Never embed MuJoCo state structures directly in `PlaybackFrame`. Data should be flat dictionaries or primitive structures that map directly to the Scene Graph.
- Always use `MotionPlayer` for delta-time updates, never manually mutate `TimelineController.current_time` when simulating continuous playback.
- Adhere to the `Interpolator` class static methods for adding new blending curves.
