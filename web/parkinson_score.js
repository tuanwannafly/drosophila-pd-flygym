export function computeParkinsonScore(features, config = {}) {
    const definitions = Array.isArray(config.features) ? config.features : [];
    const breakdown = definitions.map((definition) => {
        const values = numericSeries(features?.timeseries?.[definition.name] ?? []);
        const observed = values.length ? mean(values) : null;
        const reference = Number(definition.reference);
        const scale = Number(definition.scale);
        const direction = Number(definition.direction ?? 1);
        const normalized = observed !== null && Number.isFinite(reference) && Number.isFinite(scale) && scale !== 0
            ? direction * (observed - reference) / Math.abs(scale)
            : null;
        return {
            name: definition.name,
            weight: Number(definition.weight ?? 0),
            observed,
            reference: Number.isFinite(reference) ? reference : null,
            normalized,
            contribution: normalized === null ? null : normalized * Number(definition.weight ?? 0),
            available: normalized !== null,
        };
    });
    const available = breakdown.filter((item) => item.available);
    const weightTotal = available.reduce((sum, item) => sum + Math.abs(item.weight), 0);
    const score = weightTotal > 0 ? available.reduce((sum, item) => sum + item.contribution, 0) / weightTotal : null;
    return {
        version: 1,
        scope: 'Configurable computational index only; not a diagnosis, disease severity estimate, dopamine measure, or biological validation.',
        score,
        confidence: definitions.length ? available.length / definitions.length : 0,
        explainability: { weightedFeatures: breakdown, availableFeatureCount: available.length, configuredFeatureCount: definitions.length },
        configuration: { ...config },
    };
}

function numericSeries(values) {
    return (Array.isArray(values) ? values : []).map(Number).filter(Number.isFinite);
}

function mean(values) {
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
}
