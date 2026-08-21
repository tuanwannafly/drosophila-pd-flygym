import * as THREE from 'three';

const CHANNEL_COLORS = Object.freeze({ thorax: 0x58c4dd, com: 0xf0b429, joint: 0xd17aaf });

/** Renders only trajectory samples supplied by a pose document or DigitalFly3D. */
export class TrajectoryRenderer {
    constructor() {
        this.group = new THREE.Group();
        this.group.name = 'trajectory-overlays';
        this.visible = true;
    }

    clear() {
        while (this.group.children.length) {
            const child = this.group.children[0];
            this.group.remove(child);
            child.geometry?.dispose?.();
            child.material?.dispose?.();
        }
    }

    updateFromPose(poseDocument) {
        this.clear();
        const frames = poseDocument?.frames ?? [];
        this._addLine('thorax', frames.map((frame) => pointFrom(frame?.thorax)).filter(Boolean));
        this._addLine('com', frames.map((frame) => pointFrom(frame?.COM)).filter(Boolean));
        const jointSeries = new Map();
        frames.forEach((frame) => {
            const joints = frame?.joint_positions ?? frame?.joints ?? frame?.trajectory?.joints ?? {};
            Object.entries(joints).forEach(([name, value]) => {
                const point = pointFrom(value);
                if (point) jointSeries.set(name, [...(jointSeries.get(name) ?? []), point]);
            });
        });
        jointSeries.forEach((points, name) => this._addLine(`joint:${name}`, points));
        this.group.visible = this.visible;
    }

    updateFromDigitalFly3D(model) {
        this.clear();
        const records = model?.fly?.trajectories?.list?.() ?? [];
        records.forEach((record) => {
            const channel = String(record.metadata?.channel ?? '').toLowerCase();
            const points = flatten(record.data).map(pointFrom).filter(Boolean);
            if (points.length > 1) this._addLine(channel || 'trajectory', points, record.name);
        });
        this.group.visible = this.visible;
    }

    setVisible(visible) {
        this.visible = Boolean(visible);
        this.group.visible = this.visible;
    }

    _addLine(channel, points, name = channel) {
        if (points.length < 2) return;
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ color: CHANNEL_COLORS[channel] ?? 0x9b8cff });
        const line = new THREE.Line(geometry, material);
        line.name = name;
        line.userData.channel = channel;
        this.group.add(line);
    }

    dispose() {
        this.clear();
        this.group.removeFromParent();
    }
}

function flatten(value) {
    if (Array.isArray(value)) return value;
    if (value && typeof value === 'object') {
        if (Array.isArray(value.points)) return value.points;
        if (Array.isArray(value.frames)) return value.frames;
        return Object.values(value).flatMap((item) => flatten(item));
    }
    return [];
}

function pointFrom(value) {
    if (Array.isArray(value) && value.length >= 3) {
        const point = value.slice(0, 3).map(Number);
        return point.every(Number.isFinite) ? new THREE.Vector3(...point) : null;
    }
    if (!value || typeof value !== 'object') return null;
    const source = value.position ?? value.translation ?? value;
    const point = [source.x ?? source[0], source.y ?? source[1], source.z ?? source[2] ?? 0].map(Number);
    return point.every(Number.isFinite) ? new THREE.Vector3(...point) : null;
}
