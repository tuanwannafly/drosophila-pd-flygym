const DEFAULT_STEP_THRESHOLD = 1e-9;

export const FEATURE_NAMES = Object.freeze([
    'velocity', 'acceleration', 'angularVelocity', 'angularAcceleration',
    'comDisplacement', 'bodyOrientation', 'stepFrequency', 'stepDuration',
    'strideLength', 'strideSymmetry', 'jointRangeOfMotion', 'jointVelocity',
    'jointAcceleration', 'wingMovement', 'headMovement', 'energyEstimate',
    'trajectoryCurvature', 'turningRate',
]);

export function extractFeatureBundle(rollout, options = {}) {
    if (!rollout || typeof rollout !== 'object') {
        return unavailableBundle('No normalized rollout was provided.');
    }
    const dt = positiveNumber(rollout.timestepS) ?? 1;
    const thorax = vectorSeries(rollout.channels?.thorax);
    const com = vectorSeries(rollout.channels?.com);
    const position = thorax.length ? thorax : com;
    const velocity = differentiateVectors(position, dt);
    const acceleration = differentiateVectors(velocity, dt);
    const orientations = orientationSeries(rollout);
    const heading = orientations.map((item) => item.yaw).filter(Number.isFinite);
    const unwrappedHeading = unwrapAngles(heading);
    const angularVelocity = differentiateScalars(unwrappedHeading, dt);
    const angularAcceleration = differentiateScalars(angularVelocity, dt);
    const speed = velocity.map(magnitude);
    const comDisplacement = displacement(com.length ? com : position);
    const joints = scalarJointSeries(rollout.channels?.joint);
    const jointVelocity = mapSeries(joints, (values) => differentiateScalars(values, dt));
    const jointAcceleration = mapSeries(jointVelocity, (values) => differentiateScalars(values, dt));
    const behaviors = Array.isArray(rollout.behaviors) ? rollout.behaviors : [];
    const steps = stepEvents(behaviors, dt);
    const explicit = explicitMetrics(rollout.raw);
    const strideLength = explicit.strideLength;
    const wingMovement = movementMagnitude(rollout.channels?.wing, dt);
    const headMovement = movementMagnitude(rollout.channels?.head, dt);
    const result = {
        version: 1,
        scope: 'Computational feature extraction only; no biological interpretation is implied.',
        source: rollout.source ?? null,
        timestepS: dt,
        frameCount: rollout.frameCount ?? Math.max(position.length, heading.length),
        timeseries: {
            velocity,
            speed,
            acceleration,
            angularVelocity,
            angularAcceleration,
            heading: unwrappedHeading,
            comDisplacement,
            bodyOrientation: orientations,
            stepFrequency: steps.frequency.length ? steps.frequency : scalarOrEmpty(explicit.stepFrequency),
            stepDuration: steps.duration.length ? steps.duration : scalarOrEmpty(explicit.stepDuration),
            strideLength: scalarOrEmpty(strideLength),
            strideSymmetry: strideSymmetry(steps.events),
            jointRangeOfMotion: mapSeries(joints, (values) => range(values)),
            jointVelocity,
            jointAcceleration,
            wingMovement,
            headMovement,
            energyEstimate: speed.map((value) => value * value * dt),
            trajectoryCurvature: trajectoryCurvature(position),
            turningRate: angularVelocity.map(Math.abs),
        },
        availability: {},
        metadata: {
            stepEventCount: steps.events.length,
            explicitMetrics: explicit,
            behaviors,
            options: { ...options },
        },
    };
    result.availability = Object.fromEntries(FEATURE_NAMES.map((name) => [
        name,
        hasFeature(result.timeseries[name]),
    ]));
    return result;
}

export class FeatureCache {
    constructor(limit = 128) {
        this.limit = Math.max(1, limit);
        this.values = new Map();
    }

    get(rollout, options = {}) {
        const key = featureKey(rollout, options);
        if (this.values.has(key)) return this.values.get(key);
        const value = extractFeatureBundle(rollout, options);
        this.values.set(key, value);
        while (this.values.size > this.limit) this.values.delete(this.values.keys().next().value);
        return value;
    }

    clear() {
        this.values.clear();
    }
}

export function unavailableBundle(reason) {
    return {
        version: 1,
        scope: 'Computational feature extraction only; no biological interpretation is implied.',
        source: null,
        timestepS: null,
        frameCount: 0,
        timeseries: {},
        availability: Object.fromEntries(FEATURE_NAMES.map((name) => [name, false])),
        metadata: { unavailableReason: reason },
    };
}

function vectorSeries(series) {
    if (!Array.isArray(series)) return [];
    return series.map((item) => {
        const value = { x: Number(item?.x), y: Number(item?.y), z: Number(item?.z ?? 0) };
        return [value.x, value.y, value.z].every(Number.isFinite) ? value : null;
    }).filter(Boolean);
}

function orientationSeries(rollout) {
    const raw = Array.isArray(rollout.channels?.orientations) ? rollout.channels.orientations : [];
    if (raw.length) return raw.map((item) => ({
        yaw: finite(item?.yaw) ?? quaternionYaw(item),
        pitch: finite(item?.pitch),
        roll: finite(item?.roll),
    }));
    const heading = scalarSeries(rollout.channels?.heading);
    return heading.map((yaw) => ({ yaw, pitch: null, roll: null }));
}

function scalarJointSeries(joints) {
    if (!joints || typeof joints !== 'object' || Array.isArray(joints)) return {};
    return Object.fromEntries(Object.entries(joints).map(([name, values]) => [name, scalarSeries(values)]).filter(([, values]) => values.length));
}

function movementMagnitude(series, dt) {
    const vectors = vectorSeries(Array.isArray(series) ? series : []);
    return differentiateVectors(vectors, dt).map(magnitude);
}

function differentiateVectors(values, dt) {
    return values.map((value, index) => index === 0
        ? { x: 0, y: 0, z: 0 }
        : { x: (value.x - values[index - 1].x) / dt, y: (value.y - values[index - 1].y) / dt, z: (value.z - values[index - 1].z) / dt });
}

function differentiateScalars(values, dt) {
    return values.map((value, index) => index === 0 ? 0 : (value - values[index - 1]) / dt);
}

function trajectoryCurvature(values) {
    return values.map((value, index) => {
        if (index < 2) return 0;
        const a = values[index - 2];
        const b = values[index - 1];
        const c = value;
        const ab = distance(a, b);
        const bc = distance(b, c);
        const ac = distance(a, c);
        const areaTwice = Math.abs((b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x));
        return ab * bc * ac > 0 ? (2 * areaTwice) / (ab * bc * ac) : 0;
    });
}

function displacement(values) {
    if (!values.length) return [];
    const origin = values[0];
    return values.map((value) => ({ x: value.x - origin.x, y: value.y - origin.y, z: value.z - origin.z }));
}

function stepEvents(behaviors, dt) {
    const events = behaviors.filter((item) => /step|footfall/i.test(`${item?.type ?? ''} ${item?.label ?? ''}`));
    const frames = events.map((item) => Number(item.frame ?? item.startFrame)).filter(Number.isFinite).sort((a, b) => a - b);
    const durations = frames.slice(1).map((frame, index) => (frame - frames[index]) * dt);
    const frequency = durations.map((duration) => duration > 0 ? 1 / duration : null).filter(Number.isFinite);
    return { events, duration: durations, frequency };
}

function strideSymmetry(events) {
    const left = events.filter((item) => /left|_l\b/i.test(`${item?.label ?? ''} ${item?.body ?? ''}`)).length;
    const right = events.filter((item) => /right|_r\b/i.test(`${item?.label ?? ''} ${item?.body ?? ''}`)).length;
    return left + right > 0 ? { left, right, absoluteDifference: Math.abs(left - right), ratio: Math.min(left, right) / Math.max(left, right, 1) } : null;
}

function explicitMetrics(raw) {
    const sources = [raw, raw?.metrics, raw?.derived_locomotion_metrics, raw?.g5_measurements];
    const read = (keys) => {
        for (const source of sources) for (const key of keys) {
            const value = finite(source?.[key]);
            if (value !== null) return value;
        }
        return null;
    };
    return {
        strideLength: read(['stride_length', 'stride_length_mm']),
        stepFrequency: read(['step_frequency', 'stride_frequency', 'stride_frequency_hz']),
        stepDuration: read(['step_duration', 'step_duration_s']),
    };
}

function mapSeries(object, mapper) {
    return Object.fromEntries(Object.entries(object).map(([name, values]) => [name, mapper(values)]));
}

function range(values) {
    return values.length ? { min: Math.min(...values), max: Math.max(...values), range: Math.max(...values) - Math.min(...values) } : null;
}

function scalarOrEmpty(value) {
    return value === null ? [] : [value];
}

function scalarSeries(series) {
    if (!Array.isArray(series)) return [];
    return series.map((item) => finite(item) ?? finite(item?.value) ?? finite(item?.yaw)).filter((value) => value !== null);
}

function unwrapAngles(values) {
    if (!values.length) return [];
    const result = [values[0]];
    for (let index = 1; index < values.length; index += 1) {
        let delta = values[index] - values[index - 1];
        while (delta > Math.PI) delta -= Math.PI * 2;
        while (delta < -Math.PI) delta += Math.PI * 2;
        result.push(result[index - 1] + delta);
    }
    return result;
}

function quaternionYaw(item) {
    const qx = finite(item?.qx); const qy = finite(item?.qy); const qz = finite(item?.qz); const qw = finite(item?.qw);
    return [qx, qy, qz, qw].every((value) => value !== null)
        ? Math.atan2(2 * (qw * qz + qx * qy), 1 - 2 * (qy * qy + qz * qz))
        : null;
}

function featureKey(rollout, options) {
    return JSON.stringify([rollout?.source?.name, rollout?.frameCount, rollout?.timestepS, options]);
}

function hasFeature(value) {
    if (Array.isArray(value)) return value.length > 0;
    return value !== null && value !== undefined && Object.keys(value).length > 0;
}

function distance(a, b) {
    return Math.hypot(b.x - a.x, b.y - a.y, b.z - a.z);
}

function magnitude(value) {
    return Math.hypot(value.x, value.y, value.z);
}

function finite(value) {
    return Number.isFinite(Number(value)) ? Number(value) : null;
}

function positiveNumber(value) {
    const number = finite(value);
    return number !== null && number > 0 ? number : null;
}
