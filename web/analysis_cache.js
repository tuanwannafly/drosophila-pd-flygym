export class AnalysisCache {
    constructor({ featureLimit = 128, metricLimit = 128, comparisonLimit = 32 } = {}) {
        this.feature = new BoundedCache(featureLimit);
        this.metric = new BoundedCache(metricLimit);
        this.comparison = new BoundedCache(comparisonLimit);
    }

    clear() {
        this.feature.clear(); this.metric.clear(); this.comparison.clear();
    }
}

export class BoundedCache {
    constructor(limit = 128) { this.limit = Math.max(1, limit); this.values = new Map(); this.hits = 0; this.misses = 0; }
    get(key) {
        if (this.values.has(key)) { this.hits += 1; return this.values.get(key); }
        this.misses += 1;
        return undefined;
    }
    set(key, value) { this.values.set(key, value); while (this.values.size > this.limit) this.values.delete(this.values.keys().next().value); return value; }
    getOrSet(key, factory) { const cached = this.get(key); return cached ?? this.set(key, factory()); }
    clear() { this.values.clear(); this.hits = 0; this.misses = 0; }
    get size() { return this.values.size; }
}
