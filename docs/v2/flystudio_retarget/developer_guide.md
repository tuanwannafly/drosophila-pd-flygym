# Developer Guide

When extending Motion Retargeting:
- Retain decoupling from MuJoCo joints. A `JointPose` should only refer to the Scene Graph abstractions.
- Keep `PoseBuilder` logic deterministic. Given the same frame and profile, the resulting pose must be completely identical.
- Implement new blend algorithms in `PoseInterpolator` by using the base math provided by `Interpolator`.
