export const NORMALIZATION_SCOPES = Object.freeze(['global', 'rollout', 'experiment', 'joint', 'bodyPart']);

export function normalizeValues(values, options = {}) {
    const method = options.method ?? 'zscore';
    const finite = values.filter(Number.isFinite);
    if (!finite.length) return { values: values.map(() => null), parameters: { available: false, method } };
    const parameters = normalizationParameters(finite, method, options);
    return {
        values: values.map((value) => Number.isFinite(value) ? apply(value, parameters, method) : null),
        parameters: { available: true, method, ...parameters },
    };
}

export function normalizeFeatureBundle(bundle, options = {}) {
    const scope = options.scope ?? 'rollout';
    if (!NORMALIZATION_SCOPES.includes(scope)) throw new Error(`Unsupported normalization scope: ${scope}`);
    const timeseries = {};
    const parameterMap = {};
    for (const [name, value] of Object.entries(bundle?.timeseries ?? {})) {
        if (Array.isArray(value) && value.every((item) => Number.isFinite(item) || item === null)) {
            const normalized = normalizeValues(value.map((item) => Number(item)), { ...options, featureName: name });
            timeseries[name] = normalized.values;
            parameterMap[name] = normalized.parameters;
        } else if (value && typeof value === 'object' && !Array.isArray(value)) {
            timeseries[name] = {};
            parameterMap[name] = {};
            for (const [key, series] of Object.entries(value)) {
                if (!Array.isArray(series)) { timeseries[name][key] = series; continue; }
                const normalized = normalizeValues(series.map((item) => Number(item)), { ...options, featureName: `${name}.${key}` });
                timeseries[name][key] = normalized.values;
                parameterMap[name][key] = normalized.parameters;
            }
        } else {
            timeseries[name] = value;
        }
    }
    return {
        ...bundle,
        version: 1,
        scope: 'Computational normalization only; no biological interpretation is implied.',
        normalization: { scope, options: { ...options }, parameters: parameterMap },
        timeseries,
    };
}

export function normalizeBatch(items = [], options = {}) {
    if ((options.scope ?? 'rollout') === 'global') {
        const valuesByFeature = collectFeatureValues(items);
        const globalOptions = { ...options, globalParameters: Object.fromEntries(Object.entries(valuesByFeature).map(([name, values]) => [name, normalizationParameters(values, options.method ?? 'zscore', options)])) };
        return items.map((item) => normalizeFeatureBundle(item, globalOptions));
    }
    return items.map((item) => normalizeFeatureBundle(item, options));
}

function normalizationParameters(values, method, options) {
    if (options.globalParameters) return options.globalParameters[options.featureName] ?? basicParameters(values, method);
    return basicParameters(values, method);
}

function basicParameters(values, method) {
    const sorted = [...values].sort((a, b) => a - b);
    const mean = values.reduce((sum, value) => sum + value, 0) / values.length;
    const variance = values.reduce((sum, value) => sum + (value - mean) ** 2, 0) / values.length;
    const median = quantile(sorted, 0.5);
    const q1 = quantile(sorted, 0.25);
    const q3 = quantile(sorted, 0.75);
    return { center: method === 'robust' ? median : method === 'minmax' ? sorted[0] : mean, scale: method === 'robust' ? (q3 - q1 || 1) : method === 'minmax' ? (sorted[sorted.length - 1] - sorted[0] || 1) : (Math.sqrt(variance) || 1), min: sorted[0], max: sorted[sorted.length - 1] };
}

function apply(value, parameters, method) {
    if (method === 'minmax') return (value - parameters.center) / parameters.scale;
    return (value - parameters.center) / parameters.scale;
}

function collectFeatureValues(items) {
    const result = {};
    items.forEach((item) => Object.entries(item.timeseries ?? {}).forEach(([name, values]) => {
        if (Array.isArray(values)) result[name] = [...(result[name] ?? []), ...values.filter(Number.isFinite)];
    }));
    return result;
}

function quantile(sorted, probability) {
    const index = (sorted.length - 1) * probability;
    const lower = Math.floor(index); const upper = Math.ceil(index);
    return sorted[lower] + (sorted[upper] - sorted[lower]) * (index - lower);
}
