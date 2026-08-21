from dataclasses import dataclass
from typing import List
from .skeleton_pose import SkeletonPose
from .retarget_profile import RetargetProfile

@dataclass
class PoseValidator:
    """Validates poses against profiles."""
    profile: RetargetProfile

    def validate(self, pose: SkeletonPose) -> List[str]:
        errors = []
        expected_joints = {m.target_joint_id for m in self.profile.mappings}
        for j_id in expected_joints:
            if j_id not in pose.joints:
                errors.append(f"Missing joint: {j_id}")
        return errors
