# Tutorial

```python
from drosophila_pd.flystudio.retarget_profile import RetargetProfile
from drosophila_pd.flystudio.retarget_mapping import RetargetMapping
from drosophila_pd.flystudio.pose_builder import PoseBuilder
from drosophila_pd.flystudio.playback_frame import PlaybackFrame

# Define a profile mapping a data channel to a joint
profile = RetargetProfile(id="fly_v1")
profile.mappings.append(RetargetMapping("femur_x", "leg_joint_1"))

# Assume we get a frame from the Playback Engine
frame = PlaybackFrame(time=0.5, data={"femur_x": (1.0, 0.0, 0.0)})

# Build the pose
pose = PoseBuilder.build_from_frame(frame, profile)
print(pose.joints["leg_joint_1"].transform.translation) # (1.0, 0.0, 0.0)
```
