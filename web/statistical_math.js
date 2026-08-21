export function finiteValues(values) {
    return (Array.isArray(values) ? values : []).map(Number).filter(Number.isFinite);
}

export function mean(values) {
    const finite = finiteValues(values);
    return finite.length ? finite.reduce((sum, value) => sum + value, 0) / finite.length : null;
}

export function variance(values, sample = false) {
    const finite = finiteValues(values);
    if (finite.length < (sample ? 2 : 1)) return null;
    const center = mean(finite);
    return finite.reduce((sum, value) => sum + (value - center) ** 2, 0) / (finite.length - (sample ? 1 : 0));
}

export function standardDeviation(values, sample = false) {
    const value = variance(values, sample);
    return value === null ? null : Math.sqrt(value);
}

export function quantile(sortedValues, probability) {
    const sorted = [...sortedValues].sort((a, b) => a - b);
    if (!sorted.length) return null;
    const bounded = Math.max(0, Math.min(1, probability));
    const index = (sorted.length - 1) * bounded;
    const lower = Math.floor(index); const upper = Math.ceil(index);
    return sorted[lower] + (sorted[upper] - sorted[lower]) * (index - lower);
}

export function median(values) {
    const finite = finiteValues(values).sort((a, b) => a - b);
    return quantile(finite, 0.5);
}

export function normalCDF(value) {
    return 0.5 * (1 + erf(Number(value) / Math.sqrt(2)));
}

export function twoSidedNormalP(value) {
    return 2 * (1 - normalCDF(Math.abs(Number(value))));
}

export function erf(value) {
    const sign = value < 0 ? -1 : 1;
    const x = Math.abs(value);
    const t = 1 / (1 + 0.3275911 * x);
    const polynomial = (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t;
    return sign * (1 - polynomial * Math.exp(-x * x));
}

export function seededRandom(seed = 1) {
    let state = (Number(seed) >>> 0) || 1;
    return () => {
        state = (Math.imul(1664525, state) + 1013904223) >>> 0;
        return state / 4294967296;
    };
}

export function shuffle(values, random = Math.random) {
    const result = [...values];
    for (let index = result.length - 1; index > 0; index -= 1) {
        const swap = Math.floor(random() * (index + 1));
        [result[index], result[swap]] = [result[swap], result[index]];
    }
    return result;
}
