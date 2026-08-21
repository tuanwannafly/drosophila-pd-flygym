import { summarizeFeatureValues } from './parkinson_statistics.js';

export const COMPARISON_LABELS = Object.freeze(['Healthy', 'PD', 'Candidate', 'Control']);

export function compareFeatureBundles(items = [], options = {}) {
    const normalized = items.map((item, index) => ({
        label: item?.label ?? item?.kind ?? COMPARISON_LABELS[index] ?? `Condition ${index + 1}`,
        features: item?.features ?? item,
    })).filter((item) => item.features?.timeseries);
    const baseline = normalized[0] ?? null;
    const comparisons = normalized.slice(1).map((item) => comparePair(baseline, item, options));
    return {
        version: 1,
        scope: 'Computational comparison only; condition labels do not establish biological equivalence.',
        conditions: normalized.map(({ label, features }) => ({ label, available: features.availability ?? {} })),
        baseline: baseline?.label ?? null,
        comparisons,
        ranking: rankConditions(normalized, options.rankFeature ?? 'speed'),
    };
}

export function comparePair(baseline, candidate, options = {}) {
    const featureNames = options.features ?? ['speed', 'turningRate', 'energyEstimate', 'trajectoryCurvature'];
    const metrics = {};
    for (const name of featureNames) {
        const left = baseline?.features?.timeseries?.[name] ?? [];
        const right = candidate?.features?.timeseries?.[name] ?? [];
        const leftValues = numericSeries(left);
        const rightValues = numericSeries(right);
        metrics[name] = {
            difference: mean(rightValues) - mean(leftValues),
            absoluteDifference: Math.abs(mean(rightValues) - mean(leftValues)),
            correlation: correlation(leftValues, rightValues),
            similarity: similarity(leftValues, rightValues),
            distance: euclideanDistance(leftValues, rightValues),
            baseline: summarizeFeatureValues(leftValues),
            candidate: summarizeFeatureValues(rightValues),
        };
    }
    return { label: candidate?.label, baseline: baseline?.label, metrics };
}

export function correlation(left, right) {
    const length = Math.min(left.length, right.length);
    if (length < 2) return null;
    const a = left.slice(0, length); const b = right.slice(0, length);
    const meanA = mean(a); const meanB = mean(b);
    const numerator = a.reduce((sum, value, index) => sum + (value - meanA) * (b[index] - meanB), 0);
    const denominator = Math.sqrt(a.reduce((sum, value) => sum + (value - meanA) ** 2, 0) * b.reduce((sum, value) => sum + (value - meanB) ** 2, 0));
    return denominator > 0 ? numerator / denominator : null;
}

export function similarity(left, right) {
    const distance = euclideanDistance(left, right);
    return distance === null ? null : 1 / (1 + distance);
}

export function euclideanDistance(left, right) {
    const length = Math.min(left.length, right.length);
    if (!length) return null;
    return Math.sqrt(left.slice(0, length).reduce((sum, value, index) => sum + (value - right[index]) ** 2, 0));
}

export function rankConditions(items, feature = 'speed') {
    return items.map((item) => ({
        label: item.label,
        value: mean(numericSeries(item.features?.timeseries?.[feature] ?? [])),
    })).filter((item) => Number.isFinite(item.value)).sort((left, right) => right.value - left.value);
}

function numericSeries(values) {
    return (Array.isArray(values) ? values : []).map((value) => {
        if (Number.isFinite(Number(value))) return Number(value);
        if (value && Number.isFinite(Number(value.x))) return Math.hypot(Number(value.x), Number(value.y ?? 0), Number(value.z ?? 0));
        return null;
    }).filter(Number.isFinite);
}

function mean(values) {
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0;
}
