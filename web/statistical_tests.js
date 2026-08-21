import { finiteValues, mean, standardDeviation, twoSidedNormalP, normalCDF, seededRandom, shuffle } from './statistical_math.js';

export function welchTTest(left, right) {
    const a = finiteValues(left); const b = finiteValues(right);
    if (a.length < 2 || b.length < 2) return unavailable('Welch t-test requires at least two observations per group.');
    const meanA = mean(a); const meanB = mean(b); const varA = standardDeviation(a, true) ** 2; const varB = standardDeviation(b, true) ** 2;
    const standardError = Math.sqrt(varA / a.length + varB / b.length);
    const statistic = standardError ? (meanA - meanB) / standardError : 0;
    const degreesOfFreedom = ((varA / a.length + varB / b.length) ** 2) / (((varA / a.length) ** 2) / (a.length - 1) + ((varB / b.length) ** 2) / (b.length - 1));
    return { method: 'welch-t-test', available: true, statistic, degreesOfFreedom, pValueApprox: twoSidedNormalP(statistic), meanDifference: meanA - meanB, approximation: 'normal tail approximation for p-value' };
}

export function mannWhitney(left, right) {
    const a = finiteValues(left); const b = finiteValues(right); const combined = [...a.map((value) => ({ value, group: 0 })), ...b.map((value) => ({ value, group: 1 }))].sort((x, y) => x.value - y.value);
    if (!a.length || !b.length) return unavailable('Mann-Whitney requires two non-empty groups.');
    const rankSumA = combined.reduce((sum, item, index) => sum + (item.group === 0 ? index + 1 : 0), 0);
    const u = rankSumA - (a.length * (a.length + 1)) / 2;
    const expected = a.length * b.length / 2;
    const standardDeviationU = Math.sqrt(a.length * b.length * (a.length + b.length + 1) / 12) || 1;
    const statistic = (u - expected) / standardDeviationU;
    return { method: 'mann-whitney-u', available: true, u, statistic, pValueApprox: twoSidedNormalP(statistic), approximation: 'normal rank approximation without tie correction' };
}

export function wilcoxonSignedRank(left, right) {
    const pairs = finiteValues(left).map((value, index) => [value, Number(right[index])]).filter(([, value]) => Number.isFinite(value)).map(([a, b]) => a - b).filter((difference) => difference !== 0);
    if (!pairs.length) return unavailable('Wilcoxon signed-rank requires non-zero paired differences.');
    const ranked = pairs.map((difference) => Math.abs(difference)).sort((a, b) => a - b);
    const positive = pairs.filter((difference) => difference > 0).reduce((sum, difference) => sum + ranked.indexOf(Math.abs(difference)) + 1, 0);
    const n = pairs.length; const expected = n * (n + 1) / 4; const standardDeviationW = Math.sqrt(n * (n + 1) * (2 * n + 1) / 24) || 1;
    const statistic = (positive - expected) / standardDeviationW;
    return { method: 'wilcoxon-signed-rank', available: true, n, statistic, pValueApprox: twoSidedNormalP(statistic), approximation: 'normal signed-rank approximation without tie correction' };
}

export function kolmogorovSmirnov(left, right = null) {
    const a = finiteValues(left).sort((x, y) => x - y);
    if (!a.length) return unavailable('KS test requires finite observations.');
    if (right === null) {
        const d = Math.max(...a.map((value, index) => Math.max(Math.abs((index + 1) / a.length - normalCDF(value)), Math.abs(index / a.length - normalCDF(value)))));
        return { method: 'one-sample-ks-normal-reference', available: true, statistic: d, pValueApprox: ksPValue(d, a.length), approximation: 'standard normal reference' };
    }
    const b = finiteValues(right).sort((x, y) => x - y);
    if (!b.length) return unavailable('Two-sample KS test requires two non-empty groups.');
    const values = [...new Set([...a, ...b])]; let d = 0;
    values.forEach((value) => { d = Math.max(d, Math.abs(a.filter((item) => item <= value).length / a.length - b.filter((item) => item <= value).length / b.length)); });
    return { method: 'two-sample-ks', available: true, statistic: d, pValueApprox: ksPValue(d, (a.length * b.length) / (a.length + b.length)), approximation: 'asymptotic KS approximation' };
}

export function permutationTest(left, right, statistic = (a, b) => mean(a) - mean(b), options = {}) {
    const a = finiteValues(left); const b = finiteValues(right); const combined = [...a, ...b];
    if (!a.length || !b.length) return unavailable('Permutation test requires two non-empty groups.');
    const iterations = Math.max(1, Math.floor(options.iterations ?? 2000)); const random = seededRandom(options.seed ?? 1); const observed = statistic(a, b); let extreme = 0;
    for (let iteration = 0; iteration < iterations; iteration += 1) {
        const shuffled = shuffle(combined, random); const value = statistic(shuffled.slice(0, a.length), shuffled.slice(a.length));
        if (Math.abs(value) >= Math.abs(observed)) extreme += 1;
    }
    return { method: 'permutation-test', available: true, statistic: observed, iterations, seed: options.seed ?? 1, pValue: (extreme + 1) / (iterations + 1) };
}

function ksPValue(statistic, effectiveN) { return Math.min(1, 2 * Math.exp(-2 * effectiveN * statistic ** 2)); }
function unavailable(reason) { return { method: 'unavailable', available: false, statistic: null, pValueApprox: null, unavailableReason: reason }; }
