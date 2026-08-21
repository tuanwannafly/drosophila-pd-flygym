import json
from .skeleton_pose import SkeletonPose

class PoseSerializer:
    """Serializes poses to JSON."""

    @staticmethod
    def serialize(pose: SkeletonPose) -> str:
        return json.dumps({"id": pose.id, "joint_count": len(pose.joints)})

    @staticmethod
    def deserialize(data: str) -> dict:
        return json.loads(data)
