from .skeleton_pose import SkeletonPose
from .joint_pose import JointPose
from .transform import Transform
from .retarget_profile import RetargetProfile
from .playback_frame import PlaybackFrame

class PoseBuilder:
    """Builds poses from playback frames."""

    @staticmethod
    def build_from_frame(frame: PlaybackFrame, profile: RetargetProfile) -> SkeletonPose:
        pose = SkeletonPose(id=f"pose_{frame.time}")
        for mapping in profile.mappings:
            if mapping.source_channel in frame.data:
                val = frame.data[mapping.source_channel]
                t = Transform(translation=val if isinstance(val, tuple) else (0.0, 0.0, 0.0))
                pose.joints[mapping.target_joint_id] = JointPose(id=mapping.target_joint_id, transform=t)
        return pose
