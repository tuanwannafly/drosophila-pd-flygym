# API Reference

- `JointPose`: A single joint transform container.
- `SkeletonPose`: Complete rig pose.
- `AnimationPose`: Container for layered poses.
- `RetargetMapping`: Individual data-to-joint mapping rule.
- `RetargetProfile`: Master retargeting configuration.
- `PoseBuilder`: Factory creating `SkeletonPose`s from raw playback frames.
- `PoseInterpolator`: Math utility for cross-fading poses.
- `PoseCache`: Timestamp-keyed LRU cache for poses.
- `PoseSerializer`: JSON serializer.
- `PoseValidator`: Profile validation logic.
- `PoseStatistics`: Diagnostic tracking.
