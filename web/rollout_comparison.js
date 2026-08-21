export const COMPARISON_CONDITIONS = Object.freeze([
    'Healthy',
    'Candidate',
    'Parkinson',
]);

export function compareRollouts(rollouts, options = {}) {
    const items = normalizeRolloutList(rollouts);
    const baseline = items[0]?.rollout ?? null;
    const conditions = items.map(({ label, rollout }) => ({
        label,
        rollout,
        statistics: rollout?.statistics ?? null,
    }));
    const overlays = conditions.map(({ label, rollout }) => ({
        label,
        trajectory: copySeries(rollout?.channels?.thorax),
        speed: rollout?.statistics?.timeseries?.speed ?? [],
        angularVelocity: rollout?.statistics?.timeseries?.angularVelocity ?? [],
    }));
    const differences = baseline
        ? conditions.slice(1).map(({ label, rollout }) => ({
            label,
            trajectory: differenceSeries(baseline.channels?.thorax, rollout?.channels?.thorax),
            speed: differenceSeries(
                baseline.statistics?.timeseries?.speed,
                rollout?.statistics?.timeseries?.speed,
            ),
            angularVelocity: differenceSeries(
                baseline.statistics?.timeseries?.angularVelocity,
                rollout?.statistics?.timeseries?.angularVelocity,
            ),
            jointErrorHeatmap: jointErrorHeatmap(baseline.channels?.joint, rollout?.channels?.joint),
        }))
        : [];
    return {
        version: 1,
        scope: options.scope ?? 'Computational comparison of rollout outputs.',
        conditions,
        overlays,
        differences,
        metrics: summarizeDifferences(differences),
    };
}

export function buildComparisonReport(rollouts) {
    return compareRollouts(rollouts, {
        scope: 'Healthy/candidate comparison is computational only; labels do not establish biological equivalence.',
    });
}

function normalizeRolloutList(rollouts) {
    if (Array.isArray(rollouts)) {
        return rollouts.map((item, index) => ({
            label: item?.label ?? COMPARISON_CONDITIONS[index] ?? `Condition ${index + 1}`,
            rollout: item?.rollout ?? item,
        }));
    }
    if (rollouts && typeof rollouts === 'object') {
        return Object.entries(rollouts).map(([label, rollout]) => ({ label, rollout }));
    }
    return [];
}

function differenceSeries(left, right) {
    if (!Array.isArray(left) || !Array.isArray(right)) return [];
    const length = Math.min(left.length, right.length);
    return Array.from({ length }, (_, index) => differenceValue(left[index], right[index]));
}

function differenceValue(left, right) {
    if (Number.isFinite(Number(left)) && Number.isFinite(Number(right))) return Number(right) - Number(left);
    if (left && right && typeof left === 'object' && typeof right === 'object') {
        return Object.fromEntries(['x', 'y', 'z'].map((key) => [
            key,
            Number(right[key] ?? 0) - Number(left[key] ?? 0),
        ]));
    }
    return null;
}

function jointErrorHeatmap(left, right) {
    if (!left || !right || typeof left !== 'object' || typeof right !== 'object') return [];
    return Object.keys(left).filter((name) => right[name]).map((name) => ({
        name,
        values: differenceSeries(left[name], right[name]).map((value) => {
            if (typeof value === 'number') return Math.abs(value);
            return Math.sqrt((value?.x ?? 0) ** 2 + (value?.y ?? 0) ** 2 + (value?.z ?? 0) ** 2);
        }),
    }));
}

function summarizeDifferences(differences) {
    return differences.map((difference) => ({
        label: difference.label,
        speed: summarize(difference.speed),
        angularVelocity: summarize(difference.angularVelocity),
        trajectoryError: summarize(difference.trajectory.map(vectorMagnitude)),
    }));
}

function summarize(values) {
    const finite = values.map(Number).filter(Number.isFinite);
    if (!finite.length) return null;
    return {
        mean: finite.reduce((sum, value) => sum + value, 0) / finite.length,
        absoluteMean: finite.reduce((sum, value) => sum + Math.abs(value), 0) / finite.length,
        maxAbsolute: Math.max(...finite.map(Math.abs)),
    };
}

function vectorMagnitude(value) {
    if (Number.isFinite(Number(value))) return Number(value);
    return Math.sqrt((value?.x ?? 0) ** 2 + (value?.y ?? 0) ** 2 + (value?.z ?? 0) ** 2);
}

function copySeries(series) {
    return Array.isArray(series) ? series.map((item) => ({ ...item })) : [];
}

