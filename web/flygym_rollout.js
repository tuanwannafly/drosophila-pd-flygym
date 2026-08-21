const ROLLOUT_MARKERS = [
    'rollout',
    'flygym',
    'raw_observations',
    'observations',
    'thorax_positions',
    'joint_trajectories',
    'g5_measurements',
];

const PAYLOAD_PATHS = [
    ['frames'], ['animation', 'frames'], ['trajectory'], ['trajectories'],
    ['thorax_positions'], ['com_positions'], ['body_positions'], ['joint_trajectories'],
    ['foot_positions'], ['wing_positions'], ['head_positions'],
    ['raw_observations', 'thorax_positions'], ['observations', 'thorax_positions'],
    ['rollout', 'frames'], ['rollout', 'trajectory'],
];

const CHANNEL_ALIASES = Object.freeze({
    thorax: [
        ['thorax_positions'],
        ['trajectory'],
        ['trajectories'],
        ['trajectory', 'thorax'],
        ['trajectories', 'thorax'],
        ['raw_observations', 'thorax_positions'],
        ['observations', 'thorax_positions'],
        ['rollout', 'thorax_positions'],
    ],
    com: [
        ['com_positions'],
        ['center_of_mass'],
        ['trajectory', 'com'],
        ['trajectories', 'com'],
        ['raw_observations', 'com_positions'],
        ['observations', 'com_positions'],
    ],
    head: [
        ['head_positions'],
        ['trajectory', 'head'],
        ['trajectories', 'head'],
        ['raw_observations', 'head_positions'],
    ],
    body: [
        ['body_trajectories'],
        ['body_positions'],
        ['trajectory', 'body'],
        ['trajectories', 'body'],
        ['raw_observations', 'body_positions'],
    ],
    foot: [
        ['foot_trajectories'],
        ['foot_positions'],
        ['trajectory', 'foot'],
        ['trajectories', 'foot'],
        ['raw_observations', 'foot_positions'],
    ],
    wing: [
        ['wing_trajectories'],
        ['wing_positions'],
        ['trajectory', 'wing'],
        ['trajectories', 'wing'],
        ['raw_observations', 'wing_positions'],
    ],
    heading: [
        ['heading_rad'],
        ['heading'],
        ['raw_observations', 'heading_rad'],
        ['observations', 'heading_rad'],
    ],
    joint: [
        ['joint_trajectories'],
        ['joint_positions'],
        ['joint_angles'],
        ['trajectory', 'joint'],
        ['trajectories', 'joint'],
        ['raw_observations', 'joint_angles'],
        ['observations', 'joint_angles'],
    ],
});

export class RolloutFormatError extends Error {
    constructor(message, details = {}) {
        super(message);
        this.name = 'RolloutFormatError';
        this.details = details;
    }
}

export class FlyGymRolloutLoader {
    static async parseFile(file) {
        if (!file) throw new RolloutFormatError('No rollout file was selected.');
        if (!/\.json$/i.test(file.name || '')) {
            throw new RolloutFormatError('FlyGym rollouts must be JSON files.');
        }

        let data;
        try {
            data = JSON.parse(await file.text());
        } catch (error) {
            throw new RolloutFormatError(`Invalid rollout JSON: ${error.message}`);
        }
        return this.parseData(data, { sourceName: file.name });
    }

    static parseData(data, metadata = {}) {
        if (!this.canLoad(data)) {
            throw new RolloutFormatError(
                'JSON does not contain recognizable FlyGym rollout data.',
            );
        }
        const format = detectRolloutVersion(data);
        const channels = extractChannels(data);
        const frameCount = inferFrameCount(data, channels);
        if (frameCount < 1 && Object.keys(channels).length === 0) {
            throw new RolloutFormatError(
                'FlyGym rollout contains no frame or trajectory data.',
            );
        }

        const timing = inferTiming(data, frameCount);
        const normalized = {
            source: {
                name: metadata.sourceName ?? null,
                format,
            },
            metadata: extractMetadata(data),
            frameCount,
            timestepS: timing.timestepS,
            durationS: timing.durationS,
            fps: timing.fps,
            channels,
            behaviors: extractBehaviorTimeline(data),
            raw: data,
        };
        return Object.assign(normalized, {
            workspaceData: toWorkspaceData(normalized),
        });
    }

    static canLoad(data) {
        if (!data || typeof data !== 'object' || Array.isArray(data)) return false;
        const keys = new Set(Object.keys(data).map((key) => key.toLowerCase()));
        const hasPayload = PAYLOAD_PATHS.some((path) => {
            const value = getPath(data, path);
            return Array.isArray(value) || (value && typeof value === 'object' && Object.keys(value).length > 0);
        });
        if (keys.has('flygym') || keys.has('rollout')) return hasPayload;
        return hasPayload && ROLLOUT_MARKERS.some((marker) => keys.has(marker));
    }
}

export function detectRolloutVersion(data) {
    const version = firstValue(data, [
        ['schema_version'],
        ['format_version'],
        ['rollout_version'],
        ['metadata', 'schema_version'],
        ['metadata', 'format_version'],
        ['rollout', 'schema_version'],
        ['raw_observations', 'schema_version'],
    ]);
    const flygymVersion = firstValue(data, [
        ['flygym_version'],
        ['metadata', 'flygym_version'],
        ['environment', 'flygym_version'],
        ['versions', 'flygym'],
        ['software_versions', 'flygym'],
    ]);
    const markers = ROLLOUT_MARKERS.filter((marker) => hasPath(data, [marker]));
    return {
        format: version !== undefined ? 'flygym-rollout' : 'flygym-compatible-rollout',
        version: version === undefined ? 'legacy-unknown' : String(version),
        flygymVersion: flygymVersion === undefined ? null : String(flygymVersion),
        markers,
        confidence: version !== undefined || flygymVersion !== undefined ? 'explicit' : 'structural',
    };
}

export function toWorkspaceData(rollout) {
    const nodes = Object.keys(rollout.channels).map((channel) => ({
        id: `flygym-${channel}`,
        name: channel,
        type: 'flygym-trajectory',
        metadata: {
            source: 'FlyGym rollout',
            channel,
        },
    }));
    const frames = Array.isArray(rollout.raw?.frames)
        ? rollout.raw.frames
        : Array.isArray(rollout.raw?.animation?.frames)
            ? rollout.raw.animation.frames
            : [];
    return {
        scene: {
            name: rollout.metadata.name ?? rollout.source.name ?? 'FlyGym rollout',
            type: 'flygym-rollout',
            metadata: rollout.metadata,
        },
        nodes,
        totalFrames: rollout.frameCount,
        duration: rollout.durationS,
        animation: {
            frames,
            duration: rollout.durationS,
        },
        trajectories: rollout.channels,
        behaviors: rollout.behaviors,
    };
}

function extractChannels(data) {
    const channels = {};
    Object.entries(CHANNEL_ALIASES).forEach(([name, paths]) => {
        const value = firstPathValue(data, paths);
        if (value === undefined || value === null) return;
        const normalized = name === 'body' || name === 'foot' || name === 'wing' || name === 'joint'
            ? normalizeNamedSeries(value)
            : normalizeVectorSeries(value);
        if (normalized && hasChannelData(normalized)) channels[name] = normalized;
    });
    const orientations = firstPathValue(data, [
        ['thorax_orientations'],
        ['orientations'],
        ['trajectory', 'thorax_orientations'],
        ['raw_observations', 'thorax_orientations'],
    ]);
    if (orientations !== undefined) channels.orientations = normalizeOrientationSeries(orientations);
    return channels;
}

function normalizeNamedSeries(value) {
    if (!value || typeof value !== 'object') return null;
    if (Array.isArray(value)) {
        if (value.length === 0) return {};
        if (isVector(value[0]) || isPoint(value[0])) return { unnamed: normalizeVectorSeries(value) };
        const names = [...new Set(value.flatMap((frame) => (
            frame && typeof frame === 'object' ? Object.keys(frame) : []
        )))];
        return Object.fromEntries(names.map((name) => [
            name,
            normalizeScalarOrVectorSeries(value.map((frame) => frame?.[name])),
        ]).filter(([, series]) => hasChannelData(series)));
    }
    return Object.fromEntries(Object.entries(value)
        .map(([name, series]) => [name, normalizeScalarOrVectorSeries(series)])
        .filter(([, series]) => hasChannelData(series)));
}

function normalizeScalarOrVectorSeries(value) {
    if (Array.isArray(value) && value.every((item) => Number.isFinite(Number(item)))) {
        return value.map((item, frame) => ({ value: Number(item), frame }));
    }
    return normalizeVectorSeries(value);
}

function normalizeVectorSeries(value) {
    if (Array.isArray(value)) {
        return value.map((item, index) => normalizeVector(item, index)).filter(Boolean);
    }
    if (!value || typeof value !== 'object') return null;
    if (Array.isArray(value.frames)) return normalizeVectorSeries(value.frames);
    if (Array.isArray(value.points)) return normalizeVectorSeries(value.points);
    if (Array.isArray(value.positions)) return normalizeVectorSeries(value.positions);
    if (Array.isArray(value.x) || Array.isArray(value.y) || Array.isArray(value.z)) {
        const length = Math.max(value.x?.length ?? 0, value.y?.length ?? 0, value.z?.length ?? 0);
        return Array.from({ length }, (_, index) => normalizeVector({
            x: value.x?.[index],
            y: value.y?.[index],
            z: value.z?.[index],
        }, index)).filter(Boolean);
    }
    return null;
}

function normalizeVector(value, index) {
    if (Array.isArray(value)) {
        const numbers = value.map(Number).filter(Number.isFinite);
        if (numbers.length < 2) return null;
        return { x: numbers[0], y: numbers[1], z: numbers[2] ?? 0, frame: index };
    }
    if (!value || typeof value !== 'object') return null;
    const source = value.position ?? value.translation ?? value;
    const x = Number(source.x ?? source[0]);
    const y = Number(source.y ?? source[1]);
    const z = Number(source.z ?? source[2] ?? 0);
    if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
    const frame = Number(value.frame ?? value.frame_index ?? value.frameIndex ?? index);
    return { x, y, z: Number.isFinite(z) ? z : 0, frame: Number.isInteger(frame) ? frame : index };
}

function normalizeOrientationSeries(value) {
    if (!Array.isArray(value)) return normalizeVectorSeries(value);
    return value.map((item, index) => {
        if (Array.isArray(item)) {
            const numbers = item.map(Number);
            if (!numbers.every(Number.isFinite) || numbers.length < 3) return null;
            return numbers.length >= 4
                ? { qx: numbers[0], qy: numbers[1], qz: numbers[2], qw: numbers[3], frame: index }
                : { roll: numbers[0], pitch: numbers[1], yaw: numbers[2], frame: index };
        }
        if (!item || typeof item !== 'object') return null;
        const frame = Number(item.frame ?? item.frame_index ?? item.frameIndex ?? index);
        const quaternion = ['qx', 'qy', 'qz', 'qw'].every((key) => item[key] !== undefined);
        if (quaternion) {
            return {
                qx: Number(item.qx), qy: Number(item.qy), qz: Number(item.qz), qw: Number(item.qw),
                frame: Number.isInteger(frame) ? frame : index,
            };
        }
        const yaw = item.yaw ?? item.yaw_rad;
        if (yaw !== undefined) {
            return {
                roll: Number(item.roll ?? item.roll_rad ?? 0),
                pitch: Number(item.pitch ?? item.pitch_rad ?? 0),
                yaw: Number(yaw),
                frame: Number.isInteger(frame) ? frame : index,
            };
        }
        return normalizeVector(item, index);
    }).filter(Boolean);
}

function extractBehaviorTimeline(data) {
    const value = firstPathValue(data, [
        ['behavior'],
        ['behaviors'],
        ['behavior_events'],
        ['behavior_segments'],
        ['analysis', 'behavior'],
    ]);
    if (Array.isArray(value)) return value.map(normalizeBehavior).filter(Boolean);
    if (value && typeof value === 'object') {
        return Object.entries(value).flatMap(([label, items]) => {
            const list = Array.isArray(items) ? items : [items];
            return list.map((item) => normalizeBehavior(item, label)).filter(Boolean);
        });
    }
    return [];
}

function normalizeBehavior(value, fallbackLabel = null) {
    if (!value || typeof value !== 'object') return null;
    const start = Number(value.start_frame ?? value.startFrame ?? value.start ?? value.frame ?? 0);
    const end = Number(value.end_frame ?? value.endFrame ?? value.end ?? start);
    if (!Number.isFinite(start) || !Number.isFinite(end)) return null;
    return {
        type: value.type ?? value.kind ?? 'segment',
        label: value.label ?? value.name ?? fallbackLabel ?? 'unlabeled',
        color: value.color ?? null,
        startFrame: Math.max(0, Math.round(start)),
        endFrame: Math.max(Math.round(start), Math.round(end)),
        metadata: value.metadata ?? {},
    };
}

function extractMetadata(data) {
    const candidates = [data.metadata, data.provenance, data.environment, data.versions];
    return Object.assign({}, ...candidates.filter((item) => item && typeof item === 'object'));
}

function inferFrameCount(data, channels) {
    const candidates = [
        data.frame_count,
        data.frameCount,
        data.total_frames,
        data.totalFrames,
        data.simulation?.steps,
        data.raw_observations?.sample_count,
    ];
    const channelLengths = Object.values(channels).flatMap((channel) => {
        if (Array.isArray(channel)) return [channel.length];
        if (channel && typeof channel === 'object') {
            return Object.values(channel).filter(Array.isArray).map((series) => series.length);
        }
        return [];
    });
    const all = candidates.concat(channelLengths).map(Number).filter((value) => Number.isInteger(value) && value > 0);
    return all.length ? Math.max(...all) : 0;
}

function inferTiming(data, frameCount) {
    const timestep = Number(firstValue(data, [
        ['timestep_s'], ['timestep'], ['dt'], ['simulation', 'timestep_s'],
        ['simulation', 'timestep'], ['metadata', 'timestep_s'],
    ]));
    const duration = Number(firstValue(data, [
        ['duration_s'], ['duration'], ['simulation', 'duration_s'], ['metadata', 'duration_s'],
    ]));
    const fps = Number(firstValue(data, [['fps'], ['frame_rate'], ['metadata', 'fps']]));
    const timestepS = Number.isFinite(timestep) && timestep > 0
        ? timestep
        : Number.isFinite(fps) && fps > 0 ? 1 / fps : null;
    const durationS = Number.isFinite(duration) && duration >= 0
        ? duration
        : timestepS !== null && frameCount > 1 ? timestepS * (frameCount - 1) : null;
    return {
        timestepS,
        durationS,
        fps: timestepS ? 1 / timestepS : Number.isFinite(fps) ? fps : null,
    };
}

function hasChannelData(value) {
    return Array.isArray(value) ? value.length > 0 : value && typeof value === 'object'
        && Object.values(value).some((item) => Array.isArray(item) && item.length > 0);
}

function firstPathValue(data, paths) {
    for (const path of paths) {
        const value = getPath(data, path);
        if (value !== undefined && value !== null) return value;
    }
    return undefined;
}

function firstValue(data, paths) {
    return firstPathValue(data, paths);
}

function getPath(data, path) {
    return path.reduce((current, key) => (
        current && typeof current === 'object' ? current[key] : undefined
    ), data);
}

function hasPath(data, path) {
    return getPath(data, path) !== undefined;
}

function isVector(value) {
    return Array.isArray(value) && value.length >= 2 && value.slice(0, 3).every((item) => Number.isFinite(Number(item)));
}

function isPoint(value) {
    return Boolean(value && typeof value === 'object' && (
        value.x !== undefined || value.position !== undefined || value.translation !== undefined
    ));
}

export function flattenChannelSeries(channel) {
    if (Array.isArray(channel)) return channel;
    if (!channel || typeof channel !== 'object') return [];
    return Object.values(channel).flatMap((series) => Array.isArray(series) ? series : []);
}

export async function* streamRolloutFrames(rollout, options = {}) {
    const frames = Array.isArray(rollout?.raw?.frames)
        ? rollout.raw.frames
        : Array.isArray(rollout?.raw?.animation?.frames)
            ? rollout.raw.animation.frames
            : [];
    const start = Math.max(0, Number(options.start ?? 0));
    const end = Math.min(frames.length, Number(options.end ?? frames.length));
    const chunkSize = Math.max(1, Number(options.chunkSize ?? 1));
    for (let index = start; index < end; index += chunkSize) {
        yield frames.slice(index, Math.min(end, index + chunkSize));
        await Promise.resolve();
    }
}
