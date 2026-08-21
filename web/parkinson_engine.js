import { FeatureCache, extractFeatureBundle } from './parkinson_features.js';
import { segmentBehavior, segmentationSummary } from './parkinson_segmentation.js';
import { StatisticsCache, summarizeFeatureBundle } from './parkinson_statistics.js';
import { compareFeatureBundles } from './parkinson_comparison.js';
import { computeParkinsonScore } from './parkinson_score.js';

export class ParkinsonAnalyticsEngine {
    constructor(options = {}) {
        this.featureCache = new FeatureCache(options.featureCacheSize ?? 128);
        this.statisticsCache = new StatisticsCache(options.statisticsCacheSize ?? 128);
        this.segmentationCache = new Map();
    }

    getFeatures(rollout, options = {}) {
        return this.featureCache.get(rollout, options);
    }

    getStatistics(rollout, options = {}) {
        const features = this.getFeatures(rollout, options);
        return this.statisticsCache.get(features, options);
    }

    getSegmentation(rollout, options = {}) {
        const features = this.getFeatures(rollout, options);
        const key = JSON.stringify([rollout?.source?.name, rollout?.frameCount, options]);
        if (!this.segmentationCache.has(key)) this.segmentationCache.set(key, segmentBehavior(features, options));
        return this.segmentationCache.get(key);
    }

    analyze(rollout, options = {}) {
        const features = this.getFeatures(rollout, options);
        const segmentation = this.getSegmentation(rollout, options);
        return {
            version: 1,
            scope: 'Computational Parkinson analytics only; no biological interpretation is implied.',
            features,
            statistics: this.statisticsCache.get(features, options),
            segmentation,
            segmentationSummary: segmentationSummary(segmentation),
        };
    }

    compare(items, options = {}) {
        return compareFeatureBundles(items.map((item) => ({
            label: item.label ?? item.kind,
            features: item.features ?? this.getFeatures(item.rollout ?? item, options),
        })), options);
    }

    score(rollout, config = {}) {
        return computeParkinsonScore(this.getFeatures(rollout, config), config);
    }

    clear() {
        this.featureCache.clear();
        this.statisticsCache.clear();
        this.segmentationCache.clear();
    }
}

export { extractFeatureBundle, summarizeFeatureBundle, segmentBehavior, compareFeatureBundles, computeParkinsonScore };
