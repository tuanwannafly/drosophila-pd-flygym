import { FlyGymRolloutLoader } from './flygym_rollout.js';
import { computeRolloutStatistics } from './rollout_statistics.js';
import { AnalysisPipeline } from './analysis_pipeline.js';
import { StatisticalEngine } from './statistical_engine.js';
import { ExperimentWorkspace } from './experiment_workspace.js';
import { Workspace } from './workspace.js';
import { WorkspacePersistence, serializeWorkspace } from './workspace_persistence.js';
import { renderAnalyticsSVG } from './parkinson_visualization.js';
import { AnalyticsExporter } from './parkinson_export.js';

export class IntegrationWorkflow {
    constructor(options = {}) {
        this.workspace = options.workspace ?? new Workspace();
        this.experimentWorkspace = options.experimentWorkspace ?? new ExperimentWorkspace();
        this.pipeline = options.pipeline ?? new AnalysisPipeline(options);
        this.statistics = options.statistics ?? new StatisticalEngine(options);
        this.persistence = options.persistence ?? new WorkspacePersistence(this.workspace, options.storage ?? new MemoryStorage(), this.experimentWorkspace);
    }

    importRollout(rawData, options = {}) {
        const previous = serializeWorkspace(this.workspace, this.experimentWorkspace);
        const steps = [];
        try {
            if (!FlyGymRolloutLoader.canLoad(rawData)) throw new Error('Input is not a recognizable FlyGym-compatible rollout.');
            steps.push('import');
            const rollout = FlyGymRolloutLoader.parseData(rawData, { sourceName: options.sourceName ?? 'integration-rollout.json' });
            rollout.statistics = computeRolloutStatistics(rollout);
            steps.push('validation');
            const experiment = this.experimentWorkspace.importRollout(rollout, { name: options.name ?? rollout.source.name, kind: options.kind ?? 'Control' });
            this.workspace.loadRollout(rollout);
            steps.push('normalization');
            const analysis = this.pipeline.analyzeRollout(rollout, options.analysis ?? {});
            steps.push('quality-control', 'feature-extraction', 'analysis-pipeline');
            const statistical = this.statistics.describe(analysis.features.timeseries.speed ?? []);
            steps.push('statistical-engine');
            const comparison = this.pipeline.analyzeBatch([{ id: experiment.id, label: experiment.kind, rollout }], options.analysis ?? {}).comparisonMatrix;
            const parkinson = this.pipeline.engine.analyze(rollout, options.analysis ?? {});
            steps.push('comparison', 'parkinson-analytics');
            const visualization = {
                trajectory: renderAnalyticsSVG('trajectory', analysis.features.timeseries.comDisplacement, { title: 'Trajectory' }),
                trend: renderAnalyticsSVG('trend', { values: analysis.features.timeseries.speed }, { title: 'Speed trend' }),
            };
            steps.push('visualization');
            const report = this.statistics.report([{ name: 'speed', method: 'descriptive', statistic: statistical.mean }], { sourceName: rollout.source.name });
            const exported = {
                json: AnalyticsExporter.toJSON({ analysis, statistical }),
                markdown: AnalyticsExporter.toMarkdown('Integration statistical summary', { analysis, statistical }),
                html: AnalyticsExporter.toHTML('Integration statistical summary', { analysis, statistical }),
                csv: AnalyticsExporter.toCSV([{ feature: 'speed', mean: statistical.mean, std: statistical.std }]),
            };
            steps.push('report', 'export');
            const persistence = this.persistAndVerify();
            steps.push('workspace-persistence');
            return { overallPass: analysis.errors.length === 0 && persistence.pass, steps, experiment, rollout, analysis, statistical, comparison, parkinson, visualization, report, exported, persistence, rolledBack: false };
        } catch (error) {
            this.restoreSnapshot(previous);
            return { overallPass: false, steps, error: { name: error.name, message: error.message }, rolledBack: true, persistence: { pass: false } };
        }
    }

    analyzeBatch(rawItems = [], options = {}) {
        const parsed = rawItems.map((item) => {
            const rollout = FlyGymRolloutLoader.parseData(item.data ?? item, { sourceName: item.sourceName ?? 'batch-rollout.json' });
            rollout.statistics = computeRolloutStatistics(rollout);
            return { id: item.id, label: item.label ?? item.kind, rollout };
        });
        const batch = this.pipeline.analyzeBatch(parsed, options);
        const statistics = parsed.length > 1 ? this.statistics.compare(
            batch.reports[0].analysis.features.timeseries.speed ?? [],
            batch.reports[1].analysis.features.timeseries.speed ?? [],
            options.statistics,
        ) : null;
        return { batch, statistics, comparison: batch.comparisonMatrix, report: batch.report };
    }

    benchmark(rawData, options = {}) {
        const iterations = Math.max(1, Math.floor(options.iterations ?? 5));
        const measurements = { import: [], featureExtraction: [], statistics: [], comparison: [], export: [] };
        const memoryBefore = memoryUsage();
        for (let index = 0; index < iterations; index += 1) {
            const importStart = now();
            const rollout = FlyGymRolloutLoader.parseData(rawData, { sourceName: options.sourceName ?? 'benchmark-rollout.json' });
            rollout.statistics = computeRolloutStatistics(rollout);
            measurements.import.push(now() - importStart);
            const featureStart = now(); const analysis = this.pipeline.analyzeRollout(rollout); measurements.featureExtraction.push(now() - featureStart);
            const statStart = now(); this.statistics.describe(analysis.features.timeseries.speed ?? []); measurements.statistics.push(now() - statStart);
            const compareStart = now();
            this.statistics.compare(analysis.features.timeseries.speed ?? [], analysis.features.timeseries.speed ?? []);
            this.pipeline.analyzeBatch([{ id: 'benchmark-a', label: 'A', rollout }, { id: 'benchmark-b', label: 'B', rollout }]);
            measurements.comparison.push(now() - compareStart);
            const exportStart = now(); AnalyticsExporter.toJSON(analysis); measurements.export.push(now() - exportStart);
        }
        return { iterations, measurements, meanMs: Object.fromEntries(Object.entries(measurements).map(([name, values]) => [name, values.reduce((sum, value) => sum + value, 0) / values.length])), memory: { before: memoryBefore, after: memoryUsage() }, cache: cacheSnapshot(this.pipeline.cache) };
    }

    persistAndVerify() {
        this.persistence.save('integration-check');
        const before = JSON.stringify(this.workspace.data);
        this.persistence.restore('integration-check');
        return { pass: before === JSON.stringify(this.workspace.data), key: this.persistence.storageKey('integration-check') };
    }

    restoreSnapshot(snapshot) {
        if (!snapshot?.data) return;
        this.workspace.load(snapshot.data);
        this.workspace.rollout = snapshot.rollout ?? null;
        this.workspace.rolloutStatistics = this.workspace.rollout?.statistics ?? null;
        if (snapshot.experimentWorkspace) this.experimentWorkspace.restore(snapshot.experimentWorkspace);
    }
}

export class MemoryStorage {
    constructor() { this.values = new Map(); }
    getItem(key) { return this.values.get(key) ?? null; }
    setItem(key, value) { this.values.set(key, String(value)); }
    removeItem(key) { this.values.delete(key); }
}

function now() { return typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now(); }
function memoryUsage() { return typeof performance !== 'undefined' && typeof performance.memory?.usedJSHeapSize === 'number' ? performance.memory.usedJSHeapSize : null; }
function cacheSnapshot(cache) { return Object.fromEntries(['feature', 'metric', 'comparison'].map((name) => [name, { entries: cache[name].size, hits: cache[name].hits, misses: cache[name].misses }])); }
