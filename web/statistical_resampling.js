import { finiteValues, mean, quantile, seededRandom, shuffle } from './statistical_math.js';

export function bootstrapStatistic(values, statistic = mean, options = {}) {
    const sample = finiteValues(values);
    const iterations = Math.max(1, Math.floor(options.iterations ?? 2000));
    const random = seededRandom(options.seed ?? 1);
    const estimates = [];
    for (let iteration = 0; iteration < iterations; iteration += 1) {
        const resample = Array.from({ length: sample.length }, () => sample[Math.floor(random() * sample.length)]);
        estimates.push(statistic(resample));
    }
    const sorted = estimates.sort((a, b) => a - b);
    return {
        method: 'bootstrap-percentile',
        available: sample.length > 0,
        sampleCount: sample.length,
        iterations,
        seed: options.seed ?? 1,
        estimate: statistic(sample),
        confidenceLevel: options.confidenceLevel ?? 0.95,
        interval: percentileInterval(sorted, options.confidenceLevel ?? 0.95),
        distribution: sorted,
    };
}

export function jackknife(values, statistic = mean) {
    const sample = finiteValues(values);
    if (sample.length < 2) return { method: 'jackknife', available: false, estimates: [], estimate: null, standardError: null };
    const estimates = sample.map((_, index) => statistic(sample.filter((__, itemIndex) => itemIndex !== index)));
    const estimate = statistic(sample);
    const center = mean(estimates);
    const standardError = Math.sqrt(((estimates.reduce((sum, value) => sum + (value - center) ** 2, 0)) * (estimates.length - 1)) / estimates.length);
    return { method: 'jackknife', available: true, sampleCount: sample.length, estimates, estimate, standardError };
}

function percentileInterval(sorted, confidenceLevel) {
    if (!sorted.length) return { lower: null, upper: null };
    const alpha = (1 - confidenceLevel) / 2;
    return { lower: quantile(sorted, alpha), upper: quantile(sorted, 1 - alpha) };
}
