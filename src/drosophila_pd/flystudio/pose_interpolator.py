from .skeleton_pose import SkeletonPose
from .joint_pose import JointPose
from .transform import Transform
from .interpolator import Interpolator

class PoseInterpolator:
    """Interpolates between two poses."""

    @staticmethod
    def blend(pose_a: SkeletonPose, pose_b: SkeletonPose, t: float) -> SkeletonPose:
        result = SkeletonPose(id="blended")
        for j_id, jp_a in pose_a.joints.items():
            if j_id in pose_b.joints:
                jp_b = pose_b.joints[j_id]
                t_a = jp_a.transform.translation
                t_b = jp_b.transform.translation
                blended_t = (
                    Interpolator.linear(t_a[0], t_b[0], t),
                    Interpolator.linear(t_a[1], t_b[1], t),
                    Interpolator.linear(t_a[2], t_b[2], t)
                )
                result.joints[j_id] = JointPose(id=j_id, transform=Transform(translation=blended_t))
            else:
                result.joints[j_id] = jp_a
        return result
