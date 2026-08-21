/** Build a render descriptor from the selected imported frame. */

export class SceneBuilder {
    build(frame) {
        if (!frame) return null;
        return {
            thorax: frame.thorax,
            orientation: frame.orientation,
            COM: frame.COM,
            jointAngles: frame.joint_angles,
            jointVelocities: frame.joint_velocities,
            contacts: frame.contacts,
            trajectory: frame.trajectory,
        };
    }
}
