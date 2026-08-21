export const OUTLIER_METHODS = Object.freeze(['iqr', 'zscore', 'mad']);

export function detectOutliers(values, options = {}) {
    const method = options.method ?? 'iqr';
    if (!OUTLIER_METHODS.includes(method)) throw new Error(`Unsupported outlier method: ${method}`);
    const finite = values.map((value, index) => ({ value: Number(value), index })).filter((item) => Number.isFinite(item.value));
    if (!finite.length) return { method, outliers: [], threshold: options.threshold ?? null, available: false };
    const numbers = finite.map((item) => item.value);
    const center = mean(numbers);
    const deviations = numbers.map((value) => Math.abs(value - center));
    const medianDeviation = median(deviations);
    let lower = -Infinity; let upper = Infinity; let threshold = options.threshold;
    if (method === 'iqr') {
        const q1 = quantile(numbers, 0.25); const q3 = quantile(numbers, 0.75); const spread = q3 - q1; threshold ??= 1.5;
        lower = q1 - threshold * spread; upper = q3 + threshold * spread;
    } else if (method === 'zscore') {
        threshold ??= 3; const std = standardDeviation(numbers); lower = center - threshold * std; upper = center + threshold * std;
    } else {
        threshold ??= 3.5; const scale = medianDeviation || 1; lower = center - threshold * scale; upper = center + threshold * scale;
    }
    return { method, available: true, threshold, lower, upper, outliers: finite.filter((item) => item.value < lower || item.value > upper).map((item) => item.index), center, count: finite.length };
}

export function detectFeatureOutliers(featureBundle, options = {}) {
    return Object.fromEntries(Object.entries(featureBundle?.timeseries ?? {}).map(([name, values]) => [name, Array.isArray(values) && values.every((value) => Number.isFinite(Number(value))) ? detectOutliers(values, options) : null]));
}

function mean(values) { return values.reduce((sum, value) => sum + value, 0) / values.length; }
function standardDeviation(values) { const center = mean(values); return Math.sqrt(mean(values.map((value) => (value - center) ** 2))) || 1; }
function median(values) { return quantile([...values].sort((a, b) => a - b), 0.5); }
function quantile(sorted, probability) { const index = (sorted.length - 1) * probability; const low = Math.floor(index); const high = Math.ceil(index); return sorted[low] + (sorted[high] - sorted[low]) * (index - low); }
