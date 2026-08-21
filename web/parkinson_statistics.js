export const DEFAULT_HISTOGRAM_BINS = 10;

export function summarizeFeatureValues(values, options = {}) {
    const finite = flattenNumbers(values).filter(Number.isFinite);
    if (!finite.length) return unavailableSummary();
    const sorted = [...finite].sort((a, b) => a - b);
    const mean = finite.reduce((sum, value) => sum + value, 0) / finite.length;
    const variance = finite.reduce((sum, value) => sum + (value - mean) ** 2, 0) / finite.length;
    return {
        available: true,
        count: finite.length,
        mean,
        median: quantile(sorted, 0.5),
        variance,
        std: Math.sqrt(variance),
        min: sorted[0],
        max: sorted[sorted.length - 1],
        percentiles: Object.fromEntries((options.percentiles ?? [5, 25, 50, 75, 95]).map((percentile) => [percentile, quantile(sorted, percentile / 100)])),
        histogram: histogram(finite, options.bins ?? DEFAULT_HISTOGRAM_BINS),
        distribution: sorted,
        trend: finite.map((value, index) => ({ index, value })),
    };
}

export function summarizeFeatureBundle(bundle, options = {}) {
    const summaries = {};
    for (const [name, values] of Object.entries(bundle?.timeseries ?? {})) {
        if (name === 'bodyOrientation' || name === 'velocity' || name === 'acceleration') continue;
        if (name === 'jointRangeOfMotion' || name === 'jointVelocity' || name === 'jointAcceleration') {
            summaries[name] = Object.fromEntries(Object.entries(values).map(([joint, series]) => [joint, summarizeFeatureValues(series, options)]));
        } else {
            summaries[name] = summarizeFeatureValues(values, options);
        }
    }
    return {
        version: 1,
        scope: 'Descriptive computational statistics only; no biological interpretation is implied.',
        features: summaries,
    };
}

export class StatisticsCache {
    constructor(limit = 128) {
        this.limit = Math.max(1, limit);
        this.values = new Map();
    }

    get(bundle, options = {}) {
        const key = JSON.stringify([bundle?.source?.name, bundle?.frameCount, options]);
        if (this.values.has(key)) return this.values.get(key);
        const value = summarizeFeatureBundle(bundle, options);
        this.values.set(key, value);
        while (this.values.size > this.limit) this.values.delete(this.values.keys().next().value);
        return value;
    }

    clear() {
        this.values.clear();
    }
}

export function histogram(values, bins = DEFAULT_HISTOGRAM_BINS) {
    const finite = flattenNumbers(values).filter(Number.isFinite);
    if (!finite.length) return [];
    const count = Math.max(1, Math.floor(bins));
    const min = Math.min(...finite);
    const max = Math.max(...finite);
    const width = max === min ? 1 : (max - min) / count;
    return Array.from({ length: count }, (_, index) => ({
        min: min + index * width,
        max: index === count - 1 ? max : min + (index + 1) * width,
        count: finite.filter((value) => Math.min(count - 1, Math.floor((value - min) / width)) === index).length,
    }));
}

export function quantile(sortedValues, probability) {
    if (!sortedValues.length) return null;
    const index = (sortedValues.length - 1) * probability;
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    return sortedValues[lower] + (sortedValues[upper] - sortedValues[lower]) * (index - lower);
}

function unavailableSummary() {
    return { available: false, count: 0, mean: null, median: null, variance: null, std: null, min: null, max: null, percentiles: {}, histogram: [], distribution: [], trend: [] };
}

function flattenNumbers(values) {
    if (!Array.isArray(values)) return Object.values(values ?? {}).flatMap(flattenNumbers);
    return values.flatMap((value) => Array.isArray(value) ? flattenNumbers(value) : Number.isFinite(Number(value)) ? Number(value) : []);
}
