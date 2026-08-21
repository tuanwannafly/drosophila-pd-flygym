// Framework-neutral 3D data and motion layer for an imported DigitalFly.
// Display offsets are layout defaults only; scientific values come from trajectories.

export const DEFAULT_FLY_SKELETON = Object.freeze([
    { id: 'fly', parentId: null, displayOffset: [0, 0, 0] },
    { id: 'body', parentId: 'fly', displayOffset: [0, 0, 0] },
    { id: 'thorax', parentId: 'body', displayOffset: [0, 0, 0] },
    { id: 'abdomen', parentId: 'thorax', displayOffset: [0, -0.8, 0] },
    { id: 'head', parentId: 'thorax', displayOffset: [0, 0, 0.55] },
    { id: 'wing_L', parentId: 'thorax', displayOffset: [-0.7, 0, 0.25] },
    { id: 'wing_R', parentId: 'thorax', displayOffset: [0.7, 0, 0.25] },
    { id: 'leg_FL', parentId: 'thorax', displayOffset: [-0.55, -0.15, 0] },
    { id: 'leg_ML', parentId: 'thorax', displayOffset: [-0.65, -0.45, 0] },
    { id: 'leg_HL', parentId: 'thorax', displayOffset: [-0.45, -0.75, 0] },
    { id: 'leg_FR', parentId: 'thorax', displayOffset: [0.55, -0.15, 0] },
    { id: 'leg_MR', parentId: 'thorax', displayOffset: [0.65, -0.45, 0] },
    { id: 'leg_HR', parentId: 'thorax', displayOffset: [0.45, -0.75, 0] },
]);

export class DigitalFly3D {
    constructor({ fly, skeleton = new Skeleton3D(), metadata = {} } = {}) {
        if (!fly || typeof fly !== 'object' || !fly.id || !fly.trajectories) {
            throw new Error('DigitalFly3D requires an imported DigitalFly owner.');
        }
        this.fly = fly;
        this.id = fly.id;
        this.metadata = clone(metadata);
        this.skeleton = skeleton;
        this.frame = 0;
        this.lastFrameState = null;
        this.lastComPosition = null;
        this.skeleton.resetPose();
    }

    static fromDigitalFly(fly, options = {}) {
        return new DigitalFly3D({
            fly,
            skeleton: options.skeleton ?? Skeleton3D.fromDefaultHierarchy(),
            metadata: options.metadata,
        });
    }

    updateFrame(frame = 0) {
        const nextFrame = Math.max(0, Math.round(Number(frame) || 0));
        this.frame = nextFrame;
        this.skeleton.resetPose();
        const applied = this.applyTrajectoryFrame(nextFrame);
        this.skeleton.updateWorldTransforms();
        this.lastFrameState = this.snapshot({ applied });
        return this.lastFrameState;
    }

    applyTrajectoryFrame(frame) {
        const applied = [];
        const worldSamples = new Map();
        const jointSamples = new Map();
        this.lastComPosition = null;
        this.fly.trajectories.list().forEach((record) => {
            const value = sampleSeries(record.data, frame);
            if (value === null) return;
            const channel = String(record.metadata?.channel ?? '').toLowerCase();
            const name = String(record.metadata?.name ?? '').toLowerCase();
            const bone = findTrajectoryBone(this.skeleton, channel, name);
            if (bone && isVector3(value)) {
                worldSamples.set(bone.id, value);
                applied.push(record.name);
                return;
            }
            if (bone && isFiniteNumber(value) && channel === 'joint') {
                jointSamples.set(bone.id, Number(value));
                applied.push(record.name);
                return;
            }
            if (channel === 'com' && isVector3(value)) {
                this.lastComPosition = vector3(value);
                applied.push(record.name);
                return;
            }
            if ((channel === 'orientations' || channel === 'orientation') && Array.isArray(value) && value.length >= 4) {
                this.skeleton.getBone('fly').localTransform.quaternion = normalizeQuaternion(value);
                applied.push(record.name);
                return;
            }
            if ((channel === 'heading' || channel === 'orientations') && isFiniteNumber(value)) {
                const root = this.skeleton.getBone('fly');
                root.localTransform.quaternion = quaternionFromAxisAngle([0, 1, 0], Number(value));
                applied.push(record.name);
            }
        });

        this.skeleton.bonesInOrder().forEach((bone) => {
            const worldPosition = worldSamples.get(bone.id);
            if (worldPosition) bone.setWorldPosition(worldPosition);
            const jointAngle = jointSamples.get(bone.id);
            if (jointAngle !== undefined) {
                bone.joint.setAngle(jointAngle);
                bone.localTransform.quaternion = quaternionFromAxisAngle(bone.joint.axis, jointAngle);
            }
            this.skeleton.updateWorldTransforms();
        });
        return applied;
    }

    snapshot({ applied = [] } = {}) {
        return {
            flyId: this.id,
            frame: this.frame,
            com: this.lastComPosition ? [...this.lastComPosition] : null,
            appliedTrajectories: [...applied],
            bones: this.skeleton.bonesInOrder().map((bone) => ({
                id: bone.id,
                parentId: bone.parentId,
                localTransform: cloneTransform(bone.localTransform),
                worldTransform: cloneTransform(bone.worldTransform),
                joint: bone.joint.toJSON(),
            })),
        };
    }

    collectFrameStates(frames = []) {
        return frames.map((frame) => this.updateFrame(frame).bones.map((bone) => ({
            ...bone,
            frame,
        })));
    }

    validate() {
        const skeletonReport = validateSkeleton3D(this.skeleton);
        const trajectoryReport = validateTrajectoryOwnership(this.fly, this.id);
        return {
            valid: skeletonReport.valid && trajectoryReport.valid,
            flyId: this.id,
            skeleton: skeletonReport,
            trajectories: trajectoryReport,
            scientificScope: '3D computational representation of supplied rollout data only.',
        };
    }
}

export class Skeleton3D {
    constructor() {
        this.bones = new Map();
        this.rootId = null;
    }

    static fromDefaultHierarchy() {
        const skeleton = new Skeleton3D();
        DEFAULT_FLY_SKELETON.forEach((definition) => skeleton.addBone(definition));
        skeleton.updateWorldTransforms();
        return skeleton;
    }

    addBone({ id, name = id, parentId = null, displayOffset = [0, 0, 0], joint = {} } = {}) {
        if (!id || this.bones.has(id)) throw new Error(`Bone id must be unique: ${id}`);
        if (parentId && !this.bones.has(parentId)) throw new Error(`Parent bone not found: ${parentId}`);
        const bone = new Bone3D({ id, name, parentId, displayOffset, joint });
        this.bones.set(id, bone);
        if (parentId) this.bones.get(parentId).children.push(id);
        else if (this.rootId === null) this.rootId = id;
        else throw new Error('Skeleton3D can contain only one root bone.');
        return bone;
    }

    getBone(id) {
        const bone = this.bones.get(id);
        if (!bone) throw new Error(`Bone not found: ${id}`);
        return bone;
    }

    bonesInOrder() {
        const ordered = [];
        const visit = (id) => {
            const bone = this.bones.get(id);
            if (!bone) return;
            ordered.push(bone);
            bone.children.forEach(visit);
        };
        if (this.rootId) visit(this.rootId);
        return ordered;
    }

    resetPose() {
        this.bonesInOrder().forEach((bone) => bone.resetPose());
        this.updateWorldTransforms();
        return this;
    }

    updateWorldTransforms() {
        const visit = (bone, parent = null) => {
            bone.updateWorldTransform(parent);
            bone.children.forEach((childId) => visit(this.bones.get(childId), bone));
        };
        if (this.rootId) visit(this.bones.get(this.rootId));
        return this;
    }

    applyPose(pose = {}) {
        Object.entries(pose).forEach(([id, transform]) => {
            const bone = this.bones.get(id);
            if (bone && transform) bone.setLocalTransform(transform);
        });
        return this.updateWorldTransforms();
    }

    toJSON() {
        return { rootId: this.rootId, bones: this.bonesInOrder().map((bone) => bone.toJSON()) };
    }
}

export class Bone3D {
    constructor({ id, name, parentId, displayOffset, joint = {} }) {
        this.id = String(id);
        this.name = String(name);
        this.parentId = parentId;
        this.children = [];
        this.displayOffset = vector3(displayOffset);
        this.localTransform = createTransform(this.displayOffset, [0, 0, 0, 1]);
        this.worldTransform = createTransform([0, 0, 0], [0, 0, 0, 1]);
        this.joint = new Joint3D({
            id: joint.id ?? `joint:${this.id}`,
            axis: joint.axis ?? [0, 0, 1],
            angle: joint.angle ?? null,
        });
    }

    resetPose() {
        this.localTransform = createTransform(this.displayOffset, [0, 0, 0, 1]);
        this.worldTransform = createTransform([0, 0, 0], [0, 0, 0, 1]);
        this.worldPositionOverride = null;
        this.joint.setAngle(null);
        return this;
    }

    setLocalTransform(transform = {}) {
        if (transform.translation || transform.position) {
            this.localTransform.translation = vector3(transform.translation ?? transform.position);
        }
        if (transform.quaternion || transform.rotation) {
            this.localTransform.quaternion = normalizeQuaternion(transform.quaternion ?? transform.rotation);
        }
        return this;
    }

    setWorldPosition(position) {
        this.worldPositionOverride = vector3(position);
        return this;
    }

    updateWorldTransform(parent = null) {
        if (!parent) {
            this.worldTransform = cloneTransform(this.localTransform);
        } else {
            this.worldTransform = composeTransforms(parent.worldTransform, this.localTransform);
        }
        if (this.worldPositionOverride) this.worldTransform.translation = [...this.worldPositionOverride];
        return this;
    }

    toJSON() {
        return {
            id: this.id,
            name: this.name,
            parentId: this.parentId,
            children: [...this.children],
            displayOffset: [...this.displayOffset],
            localTransform: cloneTransform(this.localTransform),
            worldTransform: cloneTransform(this.worldTransform),
            joint: this.joint.toJSON(),
        };
    }
}

export class Joint3D {
    constructor({ id, axis = [0, 0, 1], angle = null } = {}) {
        this.id = String(id);
        this.axis = normalizeVector(axis, [0, 0, 1]);
        this.angle = angle === null ? null : Number(angle);
    }

    setAngle(angle) {
        this.angle = angle === null ? null : Number(angle);
        return this;
    }

    toJSON() { return { id: this.id, axis: [...this.axis], angle: this.angle }; }
}

export function createTransform(translation = [0, 0, 0], quaternion = [0, 0, 0, 1]) {
    return {
        translation: vector3(translation),
        quaternion: normalizeQuaternion(quaternion),
    };
}

export function composeTransforms(parent, local) {
    return createTransform(
        addVectors(parent.translation, rotateVector(parent.quaternion, local.translation)),
        multiplyQuaternions(parent.quaternion, local.quaternion),
    );
}

export function interpolateTransform(first, second, amount, { cubic = false, previous = first, next = second } = {}) {
    const t = clamp(Number(amount) || 0, 0, 1);
    const translation = cubic
        ? catmullRom(previous.translation, first.translation, second.translation, next.translation, t)
        : lerpVector(first.translation, second.translation, t);
    return createTransform(translation, slerpQuaternions(first.quaternion, second.quaternion, t));
}

export function interpolatePose(first = {}, second = {}, amount = 0, options = {}) {
    const ids = new Set([...Object.keys(first), ...Object.keys(second)]);
    const pose = {};
    ids.forEach((id) => {
        const left = first[id] ?? second[id];
        const right = second[id] ?? first[id];
        pose[id] = interpolateTransform(left, right, amount, options);
    });
    return pose;
}

export function blendPoses(poses = [], weights = []) {
    const usable = poses.filter(Boolean);
    if (usable.length === 0) return {};
    const normalizedWeights = normalizeWeights(weights, usable.length);
    const ids = new Set(usable.flatMap((pose) => Object.keys(pose)));
    const result = {};
    ids.forEach((id) => {
        const entries = usable.map((pose, index) => ({ transform: pose[id], weight: normalizedWeights[index] }))
            .filter((entry) => entry.transform);
        if (entries.length === 0) return;
        const translation = entries.reduce((sum, entry) => addVectors(sum, scaleVector(entry.transform.translation, entry.weight)), [0, 0, 0]);
        let quaternion = entries[0].transform.quaternion;
        let accumulated = entries[0].weight;
        entries.slice(1).forEach((entry) => {
            const share = entry.weight / Math.max(1e-12, accumulated + entry.weight);
            quaternion = slerpQuaternions(quaternion, entry.transform.quaternion, share);
            accumulated += entry.weight;
        });
        result[id] = createTransform(translation, quaternion);
    });
    return result;
}

export function computeSkeletonMetrics(frameStates = [], timestepS = 0) {
    const dt = Number(timestepS);
    const report = {
        frameCount: frameStates.length,
        timestepS: Number.isFinite(dt) && dt > 0 ? dt : null,
        comVelocity: [],
        comAcceleration: [],
        jointVelocity: {},
        jointAcceleration: {},
        angularVelocity: [],
        jointAngle: {},
        strideLength: null,
        strideWidth: null,
        cadence: null,
        dutyFactor: null,
        availability: {},
    };
    if (!Number.isFinite(dt) || dt <= 0 || frameStates.length < 2) return report;

    const com = frameStates.map((state) => state.com ?? state.bones?.find((bone) => bone.id === 'thorax')?.worldTransform?.translation ?? null);
    report.comVelocity = finiteDifferences(com, dt);
    report.comAcceleration = finiteDifferences(report.comVelocity, dt);

    frameStates.forEach((state, frameIndex) => {
        (state.bones ?? []).forEach((bone) => {
            const angle = bone.joint?.angle;
            if (!Number.isFinite(Number(angle))) return;
            report.jointAngle[bone.id] ??= [];
            report.jointAngle[bone.id][frameIndex] = Number(angle);
        });
    });
    Object.entries(report.jointAngle).forEach(([id, values]) => {
        report.jointVelocity[id] = finiteDifferences(values.map((value) => Number.isFinite(value) ? [value, 0, 0] : null), dt).map((vector) => vector?.[0] ?? null);
        report.jointAcceleration[id] = finiteDifferences(report.jointVelocity[id].map((value) => Number.isFinite(value) ? [value, 0, 0] : null), dt).map((vector) => vector?.[0] ?? null);
    });
    const orientations = frameStates.map((state) => state.bones?.find((bone) => bone.id === 'fly')?.worldTransform?.quaternion ?? null);
    report.angularVelocity = orientations.slice(1).map((quaternion, index) => angularVelocity(orientations[index], quaternion, dt));
    report.availability = {
        com: com.some(Boolean),
        jointAngles: Object.keys(report.jointAngle).length > 0,
        feet: frameStates.some((state) => state.feet),
        contacts: frameStates.some((state) => state.contacts),
    };
    return report;
}

export function validateSkeleton3D(skeleton) {
    const errors = [];
    const roots = [...skeleton.bones.values()].filter((bone) => bone.parentId === null);
    if (roots.length !== 1 || roots[0]?.id !== skeleton.rootId) errors.push('Skeleton must have one consistent root.');
    skeleton.bones.forEach((bone) => {
        if (bone.parentId !== null && !skeleton.bones.has(bone.parentId)) errors.push(`Missing parent: ${bone.id}`);
        bone.children.forEach((childId) => {
            if (skeleton.bones.get(childId)?.parentId !== bone.id) errors.push(`Child-parent mismatch: ${bone.id}/${childId}`);
        });
        if (!isFiniteVector(bone.localTransform.translation) || !isFiniteVector(bone.worldTransform.translation)) errors.push(`Non-finite translation: ${bone.id}`);
        if (Math.abs(lengthQuaternion(bone.localTransform.quaternion) - 1) > 1e-5) errors.push(`Non-normalized local quaternion: ${bone.id}`);
        if (Math.abs(lengthQuaternion(bone.worldTransform.quaternion) - 1) > 1e-5) errors.push(`Non-normalized world quaternion: ${bone.id}`);
    });
    if (skeleton.rootId && skeleton.bonesInOrder().length !== skeleton.bones.size) errors.push('Hierarchy contains a cycle or unreachable bone.');
    return { valid: errors.length === 0, errors, boneCount: skeleton.bones.size };
}

export function validateTrajectoryOwnership(fly, flyId = fly?.id) {
    const errors = (fly?.trajectories?.list?.() ?? [])
        .filter((record) => record.flyId !== flyId)
        .map((record) => `Trajectory is owned by ${record.flyId}: ${record.name}`);
    return { valid: errors.length === 0, errors, trajectoryCount: fly?.trajectories?.size?.() ?? 0 };
}

export function vector3(value, fallback = [0, 0, 0]) {
    if (Array.isArray(value) && value.length >= 3) return value.slice(0, 3).map(Number);
    if (value && typeof value === 'object') return [Number(value.x), Number(value.y), Number(value.z)];
    return [...fallback];
}

export function normalizeQuaternion(value) {
    const q = Array.isArray(value) && value.length >= 4
        ? value.slice(0, 4).map(Number)
        : value && typeof value === 'object'
            ? [Number(value.x), Number(value.y), Number(value.z), Number(value.w)]
            : [0, 0, 0, 1];
    const length = lengthQuaternion(q);
    return length > 1e-12 && q.every(Number.isFinite) ? q.map((item) => item / length) : [0, 0, 0, 1];
}

export function multiplyQuaternions(left, right) {
    const [x1, y1, z1, w1] = normalizeQuaternion(left);
    const [x2, y2, z2, w2] = normalizeQuaternion(right);
    return normalizeQuaternion([
        w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
        w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
        w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
    ]);
}

export function rotateVector(quaternion, vector) {
    const q = normalizeQuaternion(quaternion);
    const p = [Number(vector[0]), Number(vector[1]), Number(vector[2]), 0];
    const inverse = [-q[0], -q[1], -q[2], q[3]];
    return multiplyRaw(multiplyRaw(q, p), inverse).slice(0, 3);
}

export function slerpQuaternions(first, second, amount) {
    let left = normalizeQuaternion(first);
    let right = normalizeQuaternion(second);
    let dot = left[0] * right[0] + left[1] * right[1] + left[2] * right[2] + left[3] * right[3];
    if (dot < 0) { right = right.map((value) => -value); dot = -dot; }
    if (dot > 0.9995) return normalizeQuaternion(left.map((value, index) => value + (right[index] - value) * amount));
    const theta = Math.acos(clamp(dot, -1, 1));
    const sinTheta = Math.sin(theta);
    const firstWeight = Math.sin((1 - amount) * theta) / sinTheta;
    const secondWeight = Math.sin(amount * theta) / sinTheta;
    return normalizeQuaternion(left.map((value, index) => value * firstWeight + right[index] * secondWeight));
}

export function quaternionFromAxisAngle(axis, angle) {
    const normalizedAxis = normalizeVector(axis, [0, 1, 0]);
    const half = Number(angle) / 2;
    const sine = Math.sin(half);
    return normalizeQuaternion([normalizedAxis[0] * sine, normalizedAxis[1] * sine, normalizedAxis[2] * sine, Math.cos(half)]);
}

function findTrajectoryBone(skeleton, channel, name) {
    const normalized = `${channel}:${name}`;
    if (channel === 'thorax') return skeleton.getBone('thorax');
    if (channel === 'head') return skeleton.getBone('head');
    if (channel === 'wing') return skeleton.getBone(name.includes('l') ? 'wing_L' : name.includes('r') ? 'wing_R' : 'thorax');
    if (channel === 'foot') {
        const aliases = {
            left_front: 'leg_fl', left_middle: 'leg_ml', left_hind: 'leg_hl',
            right_front: 'leg_fr', right_middle: 'leg_mr', right_hind: 'leg_hr',
            lf: 'leg_fl', lm: 'leg_ml', lh: 'leg_hl', rf: 'leg_fr', rm: 'leg_mr', rh: 'leg_hr',
        };
        const target = aliases[name] ?? `leg_${name}`;
        return skeleton.bonesInOrder().find((bone) => bone.id.toLowerCase() === target || (name && bone.id.toLowerCase().includes(name))) ?? null;
    }
    if (channel === 'body') return skeleton.bonesInOrder().find((bone) => bone.id.toLowerCase() === name || bone.name.toLowerCase() === name) ?? null;
    if (channel === 'joint') return skeleton.bonesInOrder().find((bone) => bone.id.toLowerCase().includes(name) || bone.joint.id.toLowerCase().includes(name)) ?? null;
    void normalized;
    return null;
}

function sampleSeries(data, frame) {
    const values = Array.isArray(data) ? data : Array.isArray(data?.points) ? data.points : null;
    if (!values || values.length === 0) return null;
    const item = values[Math.min(values.length - 1, Math.max(0, frame))];
    if (item === undefined || item === null) return null;
    if (item && typeof item === 'object' && !Array.isArray(item)) return item.value ?? item.position ?? item.translation ?? item.angle ?? item;
    return item;
}

function finiteDifferences(values, dt) {
    return values.map((value, index) => {
        if (index === 0 || !isVector3(values[index - 1]) || !isVector3(value)) return null;
        return scaleVector(subtractVectors(vector3(value), vector3(values[index - 1])), 1 / dt);
    });
}

function angularVelocity(first, second, dt) {
    if (!first || !second) return null;
    const q = multiplyQuaternions([-first[0], -first[1], -first[2], first[3]], second);
    return (2 * Math.atan2(Math.hypot(q[0], q[1], q[2]), Math.abs(q[3]))) / dt;
}

function catmullRom(p0, p1, p2, p3, amount) {
    return p0.map((_, index) => 0.5 * ((2 * p1[index]) + (-p0[index] + p2[index]) * amount + (2 * p0[index] - 5 * p1[index] + 4 * p2[index] - p3[index]) * amount ** 2 + (-p0[index] + 3 * p1[index] - 3 * p2[index] + p3[index]) * amount ** 3));
}

function lerpVector(first, second, amount) { return first.map((value, index) => value + (second[index] - value) * amount); }
function addVectors(first, second) { return first.map((value, index) => value + second[index]); }
function subtractVectors(first, second) { return first.map((value, index) => value - second[index]); }
function scaleVector(value, scale) { return value.map((item) => item * scale); }
function normalizeVector(value, fallback) { const length = Math.hypot(...value); return length > 1e-12 ? value.map((item) => item / length) : [...fallback]; }
function normalizeWeights(weights, count) { const values = Array.from({ length: count }, (_, index) => Number(weights[index] ?? 1)); const sum = values.reduce((total, value) => total + Math.max(0, value), 0) || count; return values.map((value) => Math.max(0, value) / sum); }
function cloneTransform(transform) { return createTransform(transform.translation, transform.quaternion); }
function multiplyRaw(left, right) { const [x1, y1, z1, w1] = left; const [x2, y2, z2, w2] = right; return [w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]; }
function lengthQuaternion(value) { return Math.hypot(...value); }
function isVector3(value) { return (Array.isArray(value) && value.length >= 3 && isFiniteVector(value.slice(0, 3))) || (value && typeof value === 'object' && [value.x, value.y, value.z].every((item) => Number.isFinite(Number(item)))); }
function isFiniteVector(value) { return Array.isArray(value) && value.length >= 3 && value.slice(0, 3).every(Number.isFinite); }
function isFiniteNumber(value) { return Number.isFinite(Number(value)); }
function clone(value) { return value === undefined ? undefined : JSON.parse(JSON.stringify(value)); }
function clamp(value, minimum, maximum) { return Math.min(maximum, Math.max(minimum, value)); }
