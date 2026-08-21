const EPSILON = 1e-12;

export const ROLLOUT_STATISTIC_NAMES = Object.freeze([
    'velocity',
    'acceleration',
    'angular_velocity',
    'angular_acceleration',
    'stride_length',
    'stride_frequency',
    'step_count',
    'body_angle',
    'joint_range',
    'energy',
]);

export function computeRolloutStatistics(rollout) {
    if (!rollout || typeof rollout !== 'object') {
        return unavailableStatistics('No normalized rollout was provided.');
    }

    const timestepS = finitePositive(rollout.timestepS) ?? 1;
    const thorax = asVectorSeries(rollout.channels?.thorax);
    const velocity = thorax.length > 1 ? differentiateVectors(thorax, timestepS) : [];
    const acceleration = velocity.length > 1
        ? differentiateVectors(velocity, timestepS)
        : [];
    const speed = velocity.map(vectorMagnitude);
    const accelerationMagnitude = acceleration.map(vectorMagnitude);
    const heading = extractHeading(rollout);
    const angularVelocity = heading.length > 1
        ? differentiateScalars(unwrapAngles(heading), timestepS)
        : [];
    const angularAcceleration = angularVelocity.length > 1
        ? differentiateScalars(angularVelocity, timestepS)
        : [];
    const jointRange = computeJointRanges(rollout.channels?.joint);
    const explicit = findExplicitMetrics(rollout.raw);
    const stepCount = explicit.stepCount ?? countStepEvents(rollout.behaviors);
    const strideLength = explicit.strideLength;
    const strideFrequency = explicit.strideFrequency;
    const bodyAngle = extractBodyAngle(rollout, heading);
    const energy = velocity.length > 0
        ? speed.reduce((total, value) => total + value * value * timestepS, 0)
        : null;

    return {
        version: 1,
        scope: 'Computational rollout statistics; no biological interpretation is implied.',
        timestepS,
        available: {
            velocity: velocity.length > 0,
            acceleration: acceleration.length > 0,
            angularVelocity: angularVelocity.length > 0,
            angularAcceleration: angularAcceleration.length > 0,
            strideLength: strideLength !== null,
            strideFrequency: strideFrequency !== null,
            stepCount: stepCount !== null,
            bodyAngle: bodyAngle.length > 0,
            jointRange: Object.keys(jointRange).length > 0,
            energy: energy !== null,
        },
        timeseries: {
            velocity,
            speed,
            acceleration,
            accelerationMagnitude,
            heading,
            angularVelocity,
            angularAcceleration,
            bodyAngle,
        },
        summary: {
            velocity: summarizeVectors(velocity),
            speed: summarizeScalars(speed),
            acceleration: summarizeVectors(acceleration),
            angularVelocity: summarizeScalars(angularVelocity),
            angularAcceleration: summarizeScalars(angularAcceleration),
            strideLength,
            strideFrequency,
            stepCount,
            bodyAngle: summarizeScalars(bodyAngle),
            jointRange,
            energy,
        },
    };
}

export function unavailableStatistics(reason) {
    return {
        version: 1,
        scope: 'Computational rollout statistics; no biological interpretation is implied.',
        available: Object.fromEntries(ROLLOUT_STATISTIC_NAMES.map((name) => [name, false])),
        timeseries: {},
        summary: {},
        unavailableReason: reason,
    };
}

function extractHeading(rollout) {
    const explicitHeading = asScalarSeries(rollout.channels?.heading);
    if (explicitHeading.length > 0) return explicitHeading;
    const orientations = Array.isArray(rollout.channels?.orientations)
        ? rollout.channels.orientations
        : [];
    return orientations.map((orientation) => {
        if (Number.isFinite(orientation.yaw)) return orientation.yaw;
        const { qx, qy, qz, qw } = orientation;
        if ([qx, qy, qz, qw].every(Number.isFinite)) {
            return Math.atan2(
                2 * (qw * qz + qx * qy),
                1 - 2 * (qy * qy + qz * qz),
            );
        }
        return null;
    }).filter(Number.isFinite);
}

function extractBodyAngle(rollout, heading) {
    const orientations = Array.isArray(rollout.channels?.orientations)
        ? rollout.channels.orientations
        : [];
    const angles = orientations.map((orientation) => {
        if (Number.isFinite(orientation.pitch)) return orientation.pitch;
        if (Number.isFinite(orientation.roll)) return orientation.roll;
        return null;
    }).filter(Number.isFinite);
    return angles.length > 0 ? angles : heading;
}

function computeJointRanges(joints) {
    if (!joints || typeof joints !== 'object') return {};
    return Object.fromEntries(Object.entries(joints).map(([name, series]) => {
        const values = asScalarSeries(series);
        if (values.length === 0) return [name, null];
        const min = Math.min(...values);
        const max = Math.max(...values);
        return [name, {
            min,
            max,
            range: max - min,
            mean: mean(values),
            sampleCount: values.length,
        }];
    }).filter(([, value]) => value !== null));
}

function findExplicitMetrics(raw) {
    const sources = [raw, raw?.metrics, raw?.derived_locomotion_metrics, raw?.g5_measurements];
    const read = (keys) => {
        for (const source of sources) {
            if (!source || typeof source !== 'object') continue;
            for (const key of keys) {
                const value = Number(source[key]);
                if (Number.isFinite(value)) return value;
            }
        }
        return null;
    };
    return {
        strideLength: read(['stride_length', 'stride_length_mm']),
        strideFrequency: read(['stride_frequency', 'stride_frequency_hz']),
        stepCount: read(['step_count', 'steps']),
    };
}

function countStepEvents(behaviors) {
    if (!Array.isArray(behaviors)) return null;
    const count = behaviors.filter((entry) => /step|footfall/i.test(`${entry.type} ${entry.label}`)).length;
    return count > 0 ? count : null;
}

function asVectorSeries(series) {
    if (!Array.isArray(series)) return [];
    return series.map((item) => {
        const x = Number(item?.x);
        const y = Number(item?.y);
        const z = Number(item?.z ?? 0);
        return [x, y, z].every(Number.isFinite) ? { x, y, z } : null;
    }).filter(Boolean);
}

function asScalarSeries(series) {
    if (!Array.isArray(series)) return [];
    return series.map((item) => {
        if (Number.isFinite(Number(item))) return Number(item);
        if (Number.isFinite(Number(item?.value))) return Number(item.value);
        if (Number.isFinite(Number(item?.yaw))) return Number(item.yaw);
        return null;
    }).filter(Number.isFinite);
}

function differentiateVectors(values, timestepS) {
    return values.map((value, index) => {
        if (index === 0) return { x: 0, y: 0, z: 0 };
        return {
            x: (value.x - values[index - 1].x) / timestepS,
            y: (value.y - values[index - 1].y) / timestepS,
            z: (value.z - values[index - 1].z) / timestepS,
        };
    });
}

function differentiateScalars(values, timestepS) {
    return values.map((value, index) => index === 0 ? 0 : (value - values[index - 1]) / timestepS);
}

function unwrapAngles(values) {
    if (values.length === 0) return [];
    const result = [values[0]];
    for (let index = 1; index < values.length; index += 1) {
        let delta = values[index] - values[index - 1];
        while (delta > Math.PI) delta -= 2 * Math.PI;
        while (delta < -Math.PI) delta += 2 * Math.PI;
        result.push(result[index - 1] + delta);
    }
    return result;
}

function vectorMagnitude(value) {
    return Math.sqrt(value.x ** 2 + value.y ** 2 + value.z ** 2);
}

function summarizeVectors(values) {
    if (!values.length) return null;
    return summarizeScalars(values.map(vectorMagnitude));
}

function summarizeScalars(values) {
    const finite = values.filter(Number.isFinite);
    if (!finite.length) return null;
    const min = Math.min(...finite);
    const max = Math.max(...finite);
    return { min, max, mean: mean(finite), range: max - min, sampleCount: finite.length };
}

function mean(values) {
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}

function finitePositive(value) {
    const number = Number(value);
    return Number.isFinite(number) && number > EPSILON ? number : null;
}
