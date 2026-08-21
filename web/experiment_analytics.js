import { ParkinsonAnalyticsEngine } from './parkinson_engine.js';

const METRICS = Object.freeze([
    ['speed', 'Velocity'],
    ['strideFrequency', 'Stride frequency'],
    ['energy', 'Energy'],
    ['bodyAngle', 'Body angle'],
    ['jointRange', 'Joint range'],
    ['stepCount', 'Step count'],
]);

export function buildAnalyticsDashboard(entries = [], filter = {}, engine = new ParkinsonAnalyticsEngine()) {
    const rows = entries
        .filter((entry) => entry?.rollout)
        .map((entry) => summarizeEntry(entry, engine))
        .filter(Boolean);
    const summary = Object.fromEntries(METRICS.map(([key, label]) => [
        key,
        summarizeMetric(rows.map((row) => row.metrics[key]).filter(Number.isFinite), label),
    ]));
    return {
        version: 1,
        scope: 'Computational experiment summaries; no biological interpretation is implied.',
        filter: { ...filter },
        count: rows.length,
        rows,
        summary,
        histograms: Object.fromEntries(METRICS.map(([key]) => [key, histogram(rows.map((row) => row.metrics[key]))])),
        distributions: Object.fromEntries(METRICS.map(([key]) => [key, rows.map((row) => row.metrics[key]).filter(Number.isFinite)])),
        boxPlots: Object.fromEntries(METRICS.map(([key]) => [key, boxPlot(rows.map((row) => row.metrics[key]))])),
        scatter: rows.map((row) => ({ id: row.id, velocity: row.metrics.speed, energy: row.metrics.energy })),
        trend: rows.map((row, index) => ({ index, id: row.id, speed: row.metrics.speed, energy: row.metrics.energy })),
    };
}

export class AnalyticsDashboard {
    constructor(experimentWorkspace) {
        this.experimentWorkspace = experimentWorkspace;
        this.engine = new ParkinsonAnalyticsEngine();
        this.lastReport = null;
    }

    compute() {
        this.lastReport = buildAnalyticsDashboard(
            this.experimentWorkspace.filteredDataset(),
            this.experimentWorkspace.filters,
            this.engine,
        );
        return this.lastReport;
    }

    render(container) {
        if (!container) return this.compute();
        const report = this.compute();
        container.replaceChildren();
        const heading = document.createElement('h2');
        heading.textContent = 'Analytics';
        container.append(heading);
        const count = document.createElement('p');
        count.className = 'muted';
        count.textContent = `${report.count} filtered rollout${report.count === 1 ? '' : 's'}`;
        container.append(count);
        const grid = document.createElement('div');
        grid.className = 'analytics-grid';
        Object.values(report.summary).forEach((metric) => {
            const card = document.createElement('div');
            card.className = 'analytics-metric';
            card.innerHTML = `<strong>${escapeHTML(metric.label)}</strong><span>${formatNumber(metric.mean)}</span><small>n=${metric.count}</small>`;
            grid.append(card);
        });
        container.append(grid);
        return report;
    }
}

function summarizeEntry(entry, engine) {
    const statistics = entry.rollout.statistics ?? {};
    const summary = statistics.summary ?? {};
    const analysis = engine.analyze(entry.rollout);
    return {
        id: entry.id,
        experimentId: entry.experimentId,
        segmentation: analysis.segmentationSummary,
        featureAvailability: analysis.features.availability,
        metrics: {
            speed: numberOrNull(summary.speed?.mean ?? analysis.statistics.features.speed?.mean),
            strideFrequency: numberOrNull(summary.strideFrequency ?? analysis.statistics.features.stepFrequency?.mean),
            energy: numberOrNull(summary.energy ?? analysis.statistics.features.energyEstimate?.mean),
            bodyAngle: numberOrNull(summary.bodyAngle?.mean),
            jointRange: mean(Object.values(summary.jointRange ?? {}).map((item) => item?.range).filter(Number.isFinite)),
            stepCount: numberOrNull(summary.stepCount),
        },
    };
}

function summarizeMetric(values, label) {
    return {
        label,
        count: values.length,
        mean: mean(values),
        min: values.length ? Math.min(...values) : null,
        max: values.length ? Math.max(...values) : null,
    };
}

function histogram(values, bins = 8) {
    const finite = values.filter(Number.isFinite);
    if (!finite.length) return [];
    const min = Math.min(...finite);
    const max = Math.max(...finite);
    const width = max === min ? 1 : (max - min) / bins;
    return Array.from({ length: bins }, (_, index) => ({
        min: min + index * width,
        max: index === bins - 1 ? max : min + (index + 1) * width,
        count: finite.filter((value) => Math.min(bins - 1, Math.floor((value - min) / width)) === index).length,
    }));
}

function boxPlot(values) {
    const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
    return sorted.length ? {
        min: sorted[0],
        q1: quantile(sorted, 0.25),
        median: quantile(sorted, 0.5),
        q3: quantile(sorted, 0.75),
        max: sorted[sorted.length - 1],
    } : null;
}

function quantile(sorted, q) {
    const index = (sorted.length - 1) * q;
    const lower = Math.floor(index);
    const upper = Math.ceil(index);
    return sorted[lower] + (sorted[upper] - sorted[lower]) * (index - lower);
}

function mean(values) {
    return values.length ? values.reduce((total, value) => total + value, 0) / values.length : null;
}

function numberOrNull(value) {
    return Number.isFinite(Number(value)) ? Number(value) : null;
}

function formatNumber(value) {
    return Number.isFinite(value) ? value.toFixed(4) : 'n/a';
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
}
