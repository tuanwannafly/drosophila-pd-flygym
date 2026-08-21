import { ParkinsonAnalyticsEngine } from './parkinson_engine.js';
import { createDefaultFeatureGraph } from './analysis_graph.js';
import { normalizeBatch } from './analysis_normalization.js';
import { inspectBatchQuality } from './analysis_quality.js';
import { detectFeatureOutliers } from './analysis_outliers.js';
import { buildComparisonMatrix } from './analysis_matrix.js';
import { AnalysisCache } from './analysis_cache.js';

export class AnalysisPipeline {
    constructor(options = {}) {
        this.engine = options.engine ?? new ParkinsonAnalyticsEngine(options);
        this.cache = options.cache ?? new AnalysisCache(options);
        this.graph = options.graph ?? createDefaultFeatureGraph(this.engine);
        this.options = { ...options };
    }

    analyzeRollout(rollout, context = {}) {
        const key = cacheKey(rollout, context);
        const features = this.cache.feature.getOrSet(`${key}:features`, () => this.engine.getFeatures(rollout));
        return this.cache.metric.getOrSet(key, () => {
            const graph = this.graph.evaluateAll({ rollout, context }, ['features', 'statistics', 'segmentation']);
            graph.features = features;
            const quality = inspectBatchQuality([{ rollout }], context.qualityOptions).reports[0].report;
            const outliers = detectFeatureOutliers(graph.features, context.outlierOptions);
            return {
                version: 1,
                scope: 'Computational analysis pipeline only; no biological interpretation is implied.',
                source: rollout.source ?? null,
                graph: this.graph.describe(),
                features: graph.features,
                statistics: graph.statistics,
                segmentation: graph.segmentation,
                quality,
                outliers,
                warnings: [...quality.warnings],
                errors: [...quality.errors],
                suggestions: [...quality.suggestions],
            };
        });
    }

    analyzeBatch(items = [], options = {}) {
        const analyses = items.map((item) => ({ id: item.id ?? item.rollout?.source?.name ?? null, label: item.label ?? item.kind ?? null, rollout: item.rollout ?? item })).map((item) => ({ ...item, analysis: this.analyzeRollout(item.rollout, options) }));
        const normalized = normalizeBatch(analyses.map((item) => item.analysis.features), options.normalization ?? {});
        const reports = analyses.map((item, index) => ({ ...item, normalizedFeatures: normalized[index] }));
        const quality = inspectBatchQuality(reports.map((item) => ({ id: item.id, rollout: item.rollout })), options.qualityOptions);
        const comparisonKey = JSON.stringify([reports.map((item) => item.id), options.comparison ?? {}]);
        const comparisonMatrix = this.cache.comparison.getOrSet(comparisonKey, () => buildComparisonMatrix(reports.map((item) => ({ label: item.label ?? item.id, analysis: item.analysis })), options.comparison ?? {}));
        return {
            version: 1,
            scope: 'Computational batch analysis only; no biological interpretation is implied.',
            parallelReady: true,
            count: reports.length,
            reports,
            quality,
            comparisonMatrix,
            report: buildPipelineReport(reports, quality),
        };
    }

    clear() { this.cache.clear(); this.engine.clear(); }
}

export function buildPipelineReport(reports = [], quality = {}) {
    const warnings = reports.flatMap((report) => report.analysis.warnings.map((item) => ({ id: report.id, ...item })));
    const errors = reports.flatMap((report) => report.analysis.errors.map((item) => ({ id: report.id, ...item })));
    const suggestions = [...new Set(reports.flatMap((report) => report.analysis.suggestions))];
    return {
        version: 1,
        scope: 'Computational pipeline report only; no biological interpretation is implied.',
        pass: errors.length === 0,
        analyzed: reports.length,
        warnings,
        errors,
        suggestions,
        quality,
    };
}

function cacheKey(rollout, context) { return JSON.stringify([rollout?.source?.name, rollout?.frameCount, rollout?.timestepS, context]); }
