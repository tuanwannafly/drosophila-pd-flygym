import { correlation, similarity, euclideanDistance } from './parkinson_comparison.js';

export function buildComparisonMatrix(items = [], options = {}) {
    const experiments = items.map((item, index) => ({ label: item.label ?? item.kind ?? `Experiment ${index + 1}`, analysis: item.analysis ?? item }));
    const metrics = options.metrics ?? ['speed', 'turningRate', 'energyEstimate', 'trajectoryCurvature'];
    const metricMatrix = Object.fromEntries(metrics.map((metric) => [metric, matrixFor(experiments, metric)]));
    const vectors = experiments.map((item) => vectorFor(item.analysis, metrics));
    return {
        version: 1,
        scope: 'Computational experiment comparison matrix; no biological interpretation is implied.',
        experiments: experiments.map((item) => item.label),
        metrics,
        metricMatrix,
        correlationMatrix: pairwise(vectors, correlation),
        similarityMatrix: pairwise(vectors, similarity),
        distanceMatrix: pairwise(vectors, euclideanDistance),
    };
}

function matrixFor(experiments, metric) {
    return experiments.map((left) => experiments.map((right) => {
        const leftValues = numericSeries(left.analysis?.features?.timeseries?.[metric] ?? left.analysis?.timeseries?.[metric]);
        const rightValues = numericSeries(right.analysis?.features?.timeseries?.[metric] ?? right.analysis?.timeseries?.[metric]);
        return mean(rightValues) - mean(leftValues);
    }));
}

function vectorFor(analysis, metrics) {
    return metrics.map((metric) => mean(numericSeries(analysis?.features?.timeseries?.[metric] ?? analysis?.timeseries?.[metric])));
}

function pairwise(vectors, operation) {
    return vectors.map((left) => vectors.map((right) => operation(left, right)));
}

function numericSeries(values) { return (Array.isArray(values) ? values : []).map(Number).filter(Number.isFinite); }
function mean(values) { return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : 0; }
