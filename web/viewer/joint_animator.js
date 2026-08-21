import * as THREE from 'three';

export class JointAnimator {
    constructor(frames = []) { this.setFrames(frames); }

    setFrames(frames) { this.frames = Array.isArray(frames) ? frames : []; return this; }
    get frameCount() { return this.frames.length; }

    sample(frame = 0) {
        if (!this.frames.length) return null;
        const clamped = Math.max(0, Math.min(this.frames.length - 1, Number(frame) || 0));
        const leftIndex = Math.floor(clamped);
        const rightIndex = Math.min(this.frames.length - 1, leftIndex + 1);
        const alpha = clamped - leftIndex;
        const left = this.frames[leftIndex];
        const right = this.frames[rightIndex];
        if (alpha === 0 || leftIndex === rightIndex) return left;
        return { ...left, orientation: interpolateOrientation(left.orientation, right.orientation, alpha) };
    }
}

export function quaternionFromOrientation(value) {
    if (Array.isArray(value) && value.length >= 4) return new THREE.Quaternion(...value.slice(0, 4).map(Number)).normalize();
    if (value && typeof value === 'object') {
        if (['qx', 'qy', 'qz', 'qw'].every((key) => value[key] !== undefined)) {
            return new THREE.Quaternion(Number(value.qx), Number(value.qy), Number(value.qz), Number(value.qw)).normalize();
        }
        const euler = new THREE.Euler(Number(value.roll ?? 0), Number(value.pitch ?? 0), Number(value.yaw ?? value.yaw_rad ?? 0));
        return new THREE.Quaternion().setFromEuler(euler);
    }
    return null;
}

export function vectorFromValue(value) {
    if (Array.isArray(value) && value.length >= 3) {
        const vector = value.slice(0, 3).map(Number);
        return vector.every(Number.isFinite) ? vector : null;
    }
    if (!value || typeof value !== 'object') return null;
    const source = value.position ?? value.translation ?? value;
    const vector = [source.x ?? source[0], source.y ?? source[1], source.z ?? source[2] ?? 0].map(Number);
    return vector.every(Number.isFinite) ? vector : null;
}

function interpolateOrientation(left, right, alpha) {
    const a = quaternionFromOrientation(left);
    const b = quaternionFromOrientation(right);
    if (!a || !b) return alpha < 0.5 ? left : right;
    return a.slerp(b, alpha).toArray();
}
