# Playback Specification

A serialized `PlaybackSession` must contain at minimum:
- `session_id` (UUID)
- `duration` (float > 0)
- Array of `PlaybackTrack` objects.

Each `PlaybackClip` within a track maps `time` (float in seconds) to arbitrary key/value maps targeting Scene Graph Node IDs.
