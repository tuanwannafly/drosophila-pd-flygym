import { finiteValues, mean, standardDeviation, median } from './statistical_math.js';

export function effectSizes(left, right) {
    const a = finiteValues(left); const b = finiteValues(right);
    if (!a.length || !b.length) return { available: false, reason: 'Both groups require finite observations.' };
    const pooled = pooledStandardDeviation(a, b);
    const meanDifference = mean(a) - mean(b);
    const medianDifference = median(a) - median(b);
    const cliffs = cliffsDelta(a, b);
    return {
        available: true,
        meanDifference,
        cohensD: pooled ? meanDifference / pooled : null,
        glassDelta: standardDeviation(b, true) ? meanDifference / standardDeviation(b, true) : null,
        cliffsDelta: cliffs,
        rankBiserial: cliffs,
        medianDifference,
        sampleCounts: { left: a.length, right: b.length },
    };
}

function pooledStandardDeviation(a, b) {
    const varianceA = standardDeviation(a, true) ** 2; const varianceB = standardDeviation(b, true) ** 2;
    return Math.sqrt(((a.length - 1) * varianceA + (b.length - 1) * varianceB) / Math.max(1, a.length + b.length - 2));
}

function cliffsDelta(a, b) {
    let greater = 0; let less = 0;
    a.forEach((left) => b.forEach((right) => { if (left > right) greater += 1; else if (left < right) less += 1; }));
    return (greater - less) / (a.length * b.length);
}
