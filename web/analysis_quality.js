export function inspectRolloutQuality(rollout, options = {}) {
    const warnings = []; const errors = [];
    const nonFinite = []; const missing = []; const rangeViolations = [];
    if (!rollout || typeof rollout !== 'object') return invalidQuality('Rollout is missing or not an object.');
    const channels = rollout.channels ?? {};
    for (const [name, series] of Object.entries(channels)) {
        if (series === null || series === undefined) { missing.push(name); continue; }
        collectNonFinite(series, name, nonFinite);
        validateRange(series, name, options.ranges ?? {}, rangeViolations);
    }
    const lengths = channelLengths(channels);
    const uniqueLengths = [...new Set(Object.values(lengths))];
    if (uniqueLengths.length > 1) warnings.push({ code: 'CHANNEL_LENGTH_MISMATCH', lengths });
    const duplicateFrames = findDuplicateFrames(rollout);
    if (duplicateFrames.length) errors.push({ code: 'DUPLICATE_FRAMES', frames: duplicateFrames });
    const brokenTrajectory = findBrokenTrajectory(channels.thorax ?? channels.com, options.maxStepDistance);
    if (brokenTrajectory.length) warnings.push({ code: 'BROKEN_TRAJECTORY', frames: brokenTrajectory });
    if (nonFinite.length) errors.push({ code: 'NON_FINITE_VALUES', values: nonFinite });
    if (missing.length) warnings.push({ code: 'MISSING_CHANNELS', channels: missing });
    if (rangeViolations.length) warnings.push({ code: 'RANGE_VIOLATIONS', values: rangeViolations });
    const consistency = { declaredFrameCount: rollout.frameCount ?? null, channelLengths: lengths, consistent: uniqueLengths.length <= 1 };
    return {
        version: 1,
        scope: 'Computational data quality checks only; no biological interpretation is implied.',
        pass: errors.length === 0,
        warnings,
        errors,
        missing,
        nonFinite,
        rangeViolations,
        duplicateFrames,
        brokenTrajectory,
        consistency,
        suggestions: suggestionsFor({ missing, nonFinite, duplicateFrames, brokenTrajectory, rangeViolations }),
    };
}

export function inspectBatchQuality(items = [], options = {}) {
    const reports = items.map((item) => ({ id: item.id ?? item.rollout?.source?.name ?? null, report: inspectRolloutQuality(item.rollout ?? item, options) }));
    return { count: reports.length, pass: reports.every((item) => item.report.pass), reports };
}

function collectNonFinite(value, path, output) {
    if (Array.isArray(value)) return value.forEach((item, index) => collectNonFinite(item, `${path}[${index}]`, output));
    if (value && typeof value === 'object') return Object.entries(value).forEach(([key, item]) => collectNonFinite(item, `${path}.${key}`, output));
    if (value !== null && value !== undefined && typeof value === 'number' && !Number.isFinite(value)) output.push(path);
}

function validateRange(value, path, ranges, output) {
    if (Array.isArray(value)) return value.forEach((item, index) => validateRange(item, `${path}[${index}]`, ranges, output));
    if (value && typeof value === 'object') return Object.entries(value).forEach(([key, item]) => validateRange(item, `${path}.${key}`, ranges, output));
    if (typeof value !== 'number' || !Number.isFinite(value)) return;
    const range = ranges[path] ?? ranges[path.split('[')[0]];
    if (range && ((range.min !== undefined && value < range.min) || (range.max !== undefined && value > range.max))) output.push({ path, value, range });
}

function channelLengths(channels) {
    return Object.fromEntries(Object.entries(channels).map(([name, value]) => [name, Array.isArray(value) ? value.length : value && typeof value === 'object' ? Math.max(...Object.values(value).map((series) => Array.isArray(series) ? series.length : 0), 0) : 0]));
}

function findDuplicateFrames(rollout) {
    const duplicates = [];
    const inspect = (series, channel) => {
        if (!Array.isArray(series)) return;
        const seen = new Set();
        series.forEach((item, index) => {
            const frame = Number(item?.frame ?? index);
            if (seen.has(frame) && !duplicates.some((entry) => entry.channel === channel && entry.frame === frame)) duplicates.push({ channel, frame });
            seen.add(frame);
        });
    };
    Object.entries(rollout.channels ?? {}).forEach(([name, series]) => {
        if (Array.isArray(series)) inspect(series, name);
        else if (series && typeof series === 'object') Object.entries(series).forEach(([key, values]) => inspect(values, `${name}.${key}`));
    });
    return duplicates;
}

function findBrokenTrajectory(series, maxStepDistance = null) {
    if (!Array.isArray(series)) return [];
    const distances = series.map((item, index) => index === 0 ? 0 : Math.hypot(Number(item.x) - Number(series[index - 1].x), Number(item.y) - Number(series[index - 1].y), Number(item.z ?? 0) - Number(series[index - 1].z ?? 0)));
    const threshold = Number(maxStepDistance ?? 100);
    return distances.map((distance, frame) => distance > threshold ? frame : null).filter(Number.isInteger);
}

function suggestionsFor(state) {
    const suggestions = [];
    if (state.missing.length) suggestions.push('Confirm required channels are present before interpreting derived features.');
    if (state.nonFinite.length) suggestions.push('Remove or trace non-finite source values before analysis.');
    if (state.duplicateFrames.length) suggestions.push('Deduplicate or repair frame indices before temporal analysis.');
    if (state.brokenTrajectory.length) suggestions.push('Inspect large trajectory jumps and verify units/timestep.');
    return suggestions;
}

function invalidQuality(message) {
    return { version: 1, scope: 'Computational data quality checks only; no biological interpretation is implied.', pass: false, warnings: [], errors: [{ code: 'INVALID_ROLLOUT', message }], missing: [], nonFinite: [], rangeViolations: [], duplicateFrames: [], brokenTrajectory: [], consistency: { consistent: false }, suggestions: ['Provide a normalized rollout object.'] };
}
