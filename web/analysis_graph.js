export class FeatureGraph {
    constructor(nodes = []) {
        this.nodes = new Map();
        nodes.forEach((node) => this.register(node));
    }

    register({ name, dependencies = [], compute }) {
        if (!name || typeof compute !== 'function') throw new Error('Feature graph nodes require a name and compute function.');
        this.nodes.set(name, { name, dependencies: [...dependencies], compute });
        return this;
    }

    evaluate(name, context = {}, memo = new Map(), stack = []) {
        if (memo.has(name)) return memo.get(name);
        if (stack.includes(name)) throw new Error(`Feature graph cycle detected: ${[...stack, name].join(' -> ')}`);
        const node = this.nodes.get(name);
        if (!node) throw new Error(`Unknown feature graph node: ${name}`);
        const dependencies = Object.fromEntries(node.dependencies.map((dependency) => [
            dependency,
            this.evaluate(dependency, context, memo, [...stack, name]),
        ]));
        const value = node.compute({ ...context, dependencies });
        memo.set(name, value);
        return value;
    }

    evaluateAll(context = {}, names = [...this.nodes.keys()]) {
        const memo = new Map();
        return Object.fromEntries(names.map((name) => [name, this.evaluate(name, context, memo)]));
    }

    describe() {
        return [...this.nodes.values()].map(({ name, dependencies }) => ({ name, dependencies: [...dependencies] }));
    }
}

export function createDefaultFeatureGraph(engine) {
    return new FeatureGraph([
        { name: 'features', compute: ({ rollout }) => engine.getFeatures(rollout) },
        { name: 'statistics', dependencies: ['features'], compute: ({ dependencies }) => engine.statisticsCache.get(dependencies.features) },
        { name: 'segmentation', dependencies: ['features'], compute: ({ rollout, dependencies }) => engine.getSegmentation(rollout, dependencies.features.metadata?.options ?? {}) },
    ]);
}
