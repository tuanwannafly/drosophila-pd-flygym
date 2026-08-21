import { finiteValues, mean, variance, standardDeviation, quantile } from './statistical_math.js';

export function describe(values, options = {}) {
    const finite = finiteValues(values);
    if (!finite.length) return unavailable('No finite observations were provided.');
    const sorted = [...finite].sort((a, b) => a - b);
    const probabilities = options.percentiles ?? [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99];
    const center = mean(finite);
    return {
        available: true,
        count: finite.length,
        missingCount: (Array.isArray(values) ? values.length : 0) - finite.length,
        mean: center,
        median: quantile(sorted, 0.5),
        variance: variance(finite),
        sampleVariance: variance(finite, true),
        std: standardDeviation(finite),
        sampleStd: standardDeviation(finite, true),
        min: sorted[0],
        max: sorted[sorted.length - 1],
        quartile: {
            q1: quantile(sorted, 0.25),
            q2: quantile(sorted, 0.5),
            q3: quantile(sorted, 0.75),
            iqr: quantile(sorted, 0.75) - quantile(sorted, 0.25),
        },
        percentiles: Object.fromEntries(probabilities.map((probability) => [probability, quantile(sorted, probability)])),
        distribution: sorted,
    };
}

export function distribution(values, bins = 10) {
    const finite = finiteValues(values);
    if (!finite.length) return [];
    const count = Math.max(1, Math.floor(bins));
    const min = Math.min(...finite); const max = Math.max(...finite);
    const width = max === min ? 1 : (max - min) / count;
    return Array.from({ length: count }, (_, index) => ({
        min: min + index * width,
        max: index === count - 1 ? max : min + (index + 1) * width,
        count: finite.filter((value) => Math.min(count - 1, Math.floor((value - min) / width)) === index).length,
    }));
}

function unavailable(reason) {
    return { available: false, count: 0, missingCount: 0, mean: null, median: null, variance: null, sampleVariance: null, std: null, sampleStd: null, min: null, max: null, quartile: {}, percentiles: {}, distribution: [], unavailableReason: reason };
}
