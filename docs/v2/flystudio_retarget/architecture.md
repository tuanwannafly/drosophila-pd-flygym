# Architecture

The Retargeting system acts as a bridge between the Playback Engine and the Scene Graph.

- **Pose Structures**: `JointPose` (single transform) and `SkeletonPose` (dictionary of `JointPose`s) hold the retargeted values.
- **Mapping & Profiles**: `RetargetMapping` defines how a source channel (e.g. from `PlaybackFrame.data`) maps to a target joint. `RetargetProfile` bundles these mappings and base root transforms.
- **Construction**: `PoseBuilder` reads a `PlaybackFrame` and a `RetargetProfile` to construct a new `SkeletonPose`.
- **Blending**: `PoseInterpolator` blends two `SkeletonPose`s. `AnimationPose` handles layering of these blended poses.
- **Optimization**: `PoseCache` caches constructed poses keyed by timestamp.
- **Validation**: `PoseValidator` ensures all expected joints from a profile are populated.
- **Utilities**: `PoseSerializer` supports JSON export.
