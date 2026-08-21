export const DIGITAL_FLY_COMPONENTS = Object.freeze([
    'body',
    'skeleton',
    'joints',
    'bodySegments',
    'wings',
    'legs',
    'head',
    'com',
    'orientation',
    'pose',
    'motion',
    'parkinsonState',
]);

export class DigitalFly {
    constructor({ id = makeId('fly'), name = 'Digital Fly', metadata = {}, source = null } = {}) {
        this.id = String(id);
        this.name = String(name);
        this.metadata = clone(metadata);
        this.source = clone(source);
        this.body = new BodyModel();
        this.skeleton = new SkeletonModel();
        this.joints = new JointModel();
        this.bodySegments = this.body.segments;
        this.wings = new WingModel();
        this.legs = new LegModel();
        this.head = new HeadModel();
        this.com = new COMModel();
        this.orientation = new OrientationModel();
        this.pose = new PoseModel();
        this.motion = new MotionModel();
        this.parkinsonState = new ParkinsonStateModel();
        this.trajectories = new TrajectoryRegistry(this.id);
    }

    static fromRollout(rollout, options = {}) {
        if (!rollout || typeof rollout !== 'object' || !rollout.channels || typeof rollout.channels !== 'object') {
            throw new Error('A normalized rollout with channels is required.');
        }
        const fly = new DigitalFly({
            id: options.id,
            name: options.name ?? rollout.metadata?.name ?? rollout.source?.name ?? 'Digital Fly',
            metadata: { ...rollout.metadata, ...(options.metadata ?? {}) },
            source: rollout.source,
        });
        fly.ingestRollout(rollout);
        return fly;
    }

    ingestRollout(rollout) {
        this.source = clone(rollout.source ?? this.source);
        this.motion.configure({
            frameCount: rollout.frameCount ?? null,
            timestepS: rollout.timestepS ?? null,
            durationS: rollout.durationS ?? null,
            fps: rollout.fps ?? null,
        });
        Object.entries(rollout.channels ?? {}).forEach(([channel, value]) => this.ingestChannel(channel, value));
        return this;
    }

    ingestChannel(channel, value) {
        if (value === null || value === undefined) return [];
        const entries = isNamedSeries(value) ? Object.entries(value) : [['', value]];
        return entries.map(([name, series]) => {
            const trajectoryName = `rollout:${channel}${name ? `:${name}` : ''}`;
            this.attachTrajectory(trajectoryName, series, { channel, name });
            this.bindChannel(channel, name, trajectoryName);
            return trajectoryName;
        });
    }

    attachTrajectory(name, data, metadata = {}) {
        return this.trajectories.attach(name, data, metadata);
    }

    bindChannel(channel, name, trajectoryName) {
        const safeName = name || channel;
        this.trajectories.bind(trajectoryName, `${channel}:${safeName}`);
        if (channel === 'thorax') {
            const node = this.body.addSegment({ id: 'thorax', name: 'thorax', metadata: { observedChannel: channel } });
            this.skeleton.addBone({ id: 'thorax', name: 'thorax', metadata: { observedChannel: channel } });
            node.addTrajectory(trajectoryName);
            this.skeleton.bind('thorax', trajectoryName);
            this.pose.addTrajectory(trajectoryName);
        } else if (channel === 'body') {
            const node = this.body.addSegment({ id: `body-${slug(safeName)}`, name: safeName, metadata: { observedChannel: channel } });
            node.addTrajectory(trajectoryName);
            this.skeleton.addBone({ id: `body-${slug(safeName)}`, name: safeName, metadata: { observedChannel: channel } });
        } else if (channel === 'joint') {
            const joint = this.joints.addJoint({ id: `joint-${slug(safeName)}`, name: safeName, metadata: { observedChannel: channel } });
            joint.addTrajectory(trajectoryName);
            this.skeleton.addBone({ id: `joint-${slug(safeName)}`, name: safeName, metadata: { observedChannel: channel } });
            this.motion.addTrajectory(trajectoryName);
        } else if (channel === 'wing') {
            const wing = this.wings.addPart({ id: `wing-${slug(safeName)}`, name: safeName, metadata: { observedChannel: channel } });
            wing.addTrajectory(trajectoryName);
            this.motion.addTrajectory(trajectoryName);
        } else if (channel === 'foot') {
            const leg = this.legs.addPart({ id: `leg-${slug(safeName)}`, name: safeName, metadata: { observedChannel: channel } });
            leg.addTrajectory(trajectoryName);
            this.motion.addTrajectory(trajectoryName);
        } else if (channel === 'head') {
            this.head.addTrajectory(trajectoryName);
            this.pose.addTrajectory(trajectoryName);
        } else if (channel === 'com') {
            this.com.addTrajectory(trajectoryName);
            this.pose.addTrajectory(trajectoryName);
        } else if (channel === 'orientations' || channel === 'heading') {
            this.orientation.addTrajectory(trajectoryName);
            this.pose.addTrajectory(trajectoryName);
        } else {
            this.motion.addTrajectory(trajectoryName);
        }
    }

    getTrajectory(name) {
        return this.trajectories.get(name);
    }

    validate() {
        const missingFlyOwner = this.trajectories.list().filter((trajectory) => trajectory.flyId !== this.id).map((trajectory) => trajectory.name);
        const missingReferences = this.trajectories.list().filter((trajectory) => trajectory.bindings.length === 0).map((trajectory) => trajectory.name);
        return {
            valid: missingFlyOwner.length === 0,
            flyId: this.id,
            trajectoryCount: this.trajectories.size(),
            missingFlyOwner,
            unboundTrajectories: missingReferences,
            scientificScope: 'Digital representation of supplied computational rollout data only.',
        };
    }

    toJSON() {
        return {
            version: 1,
            id: this.id,
            name: this.name,
            metadata: clone(this.metadata),
            source: clone(this.source),
            body: this.body.toJSON(),
            skeleton: this.skeleton.toJSON(),
            joints: this.joints.toJSON(),
            wings: this.wings.toJSON(),
            legs: this.legs.toJSON(),
            head: this.head.toJSON(),
            com: this.com.toJSON(),
            orientation: this.orientation.toJSON(),
            pose: this.pose.toJSON(),
            motion: this.motion.toJSON(),
            parkinsonState: this.parkinsonState.toJSON(),
            trajectories: this.trajectories.toJSON(),
        };
    }

    static fromJSON(data = {}) {
        const fly = new DigitalFly({ id: data.id, name: data.name, metadata: data.metadata, source: data.source });
        fly.body.restore(data.body);
        fly.skeleton.restore(data.skeleton);
        fly.joints.restore(data.joints);
        fly.wings.restore(data.wings);
        fly.legs.restore(data.legs);
        fly.head.restore(data.head);
        fly.com.restore(data.com);
        fly.orientation.restore(data.orientation);
        fly.pose.restore(data.pose);
        fly.motion.restore(data.motion);
        fly.parkinsonState.restore(data.parkinsonState);
        fly.trajectories.restore(data.trajectories);
        return fly;
    }
}

export class ComponentModel {
    constructor(type, name = type) { this.id = makeId(type); this.type = type; this.name = name; this.metadata = {}; this.trajectoryRefs = []; }
    addTrajectory(name) { if (!this.trajectoryRefs.includes(name)) this.trajectoryRefs.push(name); return this; }
    toJSON() { return { id: this.id, type: this.type, name: this.name, metadata: clone(this.metadata), trajectoryRefs: [...this.trajectoryRefs] }; }
    restore(data = {}) { this.id = data.id ?? this.id; this.type = data.type ?? this.type; this.name = data.name ?? this.name; this.metadata = clone(data.metadata ?? {}); this.trajectoryRefs = [...(data.trajectoryRefs ?? [])]; return this; }
}

export class ComponentCollection {
    constructor(type) { this.type = type; this.parts = new Map(); }
    add(node = {}) { const item = new ComponentModel(this.type, node.name ?? node.id ?? this.type); Object.assign(item, { id: node.id ?? makeId(this.type), metadata: clone(node.metadata ?? {}) }); this.parts.set(item.id, item); return item; }
    toJSON() { return { type: this.type, parts: [...this.parts.values()].map((part) => part.toJSON()) }; }
    restore(data = {}) { this.parts = new Map((data.parts ?? []).map((part) => { const item = new ComponentModel(data.type ?? this.type, part.name); Object.assign(item, part); return [item.id, item]; })); return this; }
}

export class BodyModel {
    constructor() { this.type = 'body'; this.segments = new HierarchyModel('body-segment'); }
    addSegment(node) { return this.segments.add(node); }
    toJSON() { return { type: this.type, segments: this.segments.toJSON() }; }
    restore(data = {}) { this.segments.restore(data.segments); return this; }
}

export class SkeletonModel {
    constructor() { this.type = 'skeleton'; this.bones = new HierarchyModel('bone'); }
    addBone(node) { return this.bones.add(node); }
    bind(id, trajectoryName) { return this.bones.bind(id, trajectoryName); }
    toJSON() { return { type: this.type, bones: this.bones.toJSON() }; }
    restore(data = {}) { this.bones.restore(data.bones); return this; }
}

export class JointModel {
    constructor() { this.type = 'joints'; this.joints = new ComponentCollection('joint'); }
    addJoint(node) { return this.joints.add(node); }
    toJSON() { return { type: this.type, joints: this.joints.toJSON() }; }
    restore(data = {}) { this.joints.restore(data.joints); return this; }
}

export class WingModel extends ComponentCollection { constructor() { super('wing'); } }
export class LegModel extends ComponentCollection { constructor() { super('leg'); } }
export class HeadModel extends ComponentModel { constructor() { super('head', 'head'); } }
export class COMModel extends ComponentModel { constructor() { super('com', 'center-of-mass'); } }
export class OrientationModel extends ComponentModel { constructor() { super('orientation', 'orientation'); } }
export class PoseModel extends ComponentModel { constructor() { super('pose', 'pose'); } }

export class MotionModel extends ComponentModel {
    constructor() { super('motion', 'motion'); this.frameCount = null; this.timestepS = null; this.durationS = null; this.fps = null; }
    configure(values = {}) { Object.assign(this, values); return this; }
    toJSON() { return { ...super.toJSON(), frameCount: this.frameCount, timestepS: this.timestepS, durationS: this.durationS, fps: this.fps }; }
    restore(data = {}) { super.restore(data); return this.configure(data); }
}

export class ParkinsonStateModel {
    constructor() { this.type = 'computational-parkinson-state'; this.state = 'unassigned'; this.parameters = {}; this.provenance = null; }
    setState(state, parameters = {}, provenance = null) { this.state = String(state); this.parameters = clone(parameters); this.provenance = clone(provenance); return this; }
    toJSON() { return { type: this.type, state: this.state, parameters: clone(this.parameters), provenance: clone(this.provenance), scope: 'Computational state metadata only; no biological interpretation.' }; }
    restore(data = {}) { return this.setState(data.state ?? 'unassigned', data.parameters ?? {}, data.provenance ?? null); }
}

export class HierarchyModel {
    constructor(type) { this.type = type; this.nodes = new Map(); }
    add(node = {}) {
        const id = node.id ?? makeId(this.type);
        const item = this.nodes.get(id) ?? { id, name: node.name ?? id ?? this.type, parentId: node.parentId ?? null, metadata: clone(node.metadata ?? {}), trajectoryRefs: [] };
        if (node.name !== undefined) item.name = node.name;
        if (node.parentId !== undefined) item.parentId = node.parentId;
        if (node.metadata !== undefined) item.metadata = clone(node.metadata);
        this.nodes.set(item.id, item);
        return { ...item, addTrajectory: (name) => { this.bind(item.id, name); return item; } };
    }
    bind(id, name) { const item = this.nodes.get(id); if (!item) throw new Error(`${this.type} node not found: ${id}`); if (!item.trajectoryRefs.includes(name)) item.trajectoryRefs.push(name); return item; }
    toJSON() { return { type: this.type, nodes: [...this.nodes.values()].map(clone) }; }
    restore(data = {}) { this.nodes = new Map((data.nodes ?? []).map((node) => [node.id, clone(node)])); return this; }
}

export class TrajectoryRegistry {
    constructor(flyId) { this.flyId = flyId; this.records = new Map(); }
    attach(name, data, metadata = {}) {
        if (!name || data === undefined || data === null) throw new Error('Trajectory name and data are required.');
        if (this.records.has(name)) throw new Error(`Trajectory already attached: ${name}`);
        const record = { name, flyId: this.flyId, data, metadata: clone(metadata), bindings: [] };
        this.records.set(name, record);
        return record;
    }
    bind(name, component) { const record = this.require(name); if (!record.bindings.includes(component)) record.bindings.push(component); return record; }
    get(name) { return this.records.get(name) ?? null; }
    require(name) { const record = this.get(name); if (!record) throw new Error(`Trajectory not found: ${name}`); return record; }
    list() { return [...this.records.values()]; }
    size() { return this.records.size; }
    toJSON() { return { flyId: this.flyId, records: this.list().map((record) => ({ ...record, data: clone(record.data) })) }; }
    restore(data = {}) { this.flyId = data.flyId ?? this.flyId; this.records = new Map((data.records ?? []).map((record) => [record.name, clone(record)])); return this; }
}

function isNamedSeries(value) {
    return value && !Array.isArray(value) && typeof value === 'object' && Object.values(value).some((entry) => Array.isArray(entry) || (entry && typeof entry === 'object'));
}

function slug(value) { return String(value).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '') || 'unnamed'; }
function makeId(prefix) { return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`; }
function clone(value) { return value === undefined ? undefined : JSON.parse(JSON.stringify(value)); }
