export class FrameCache {
    constructor(limit = 120) {
        this.limit = Math.max(1, limit);
        this.values = new Map();
    }

    get(frame) {
        const value = this.values.get(frame);
        if (value !== undefined) {
            this.values.delete(frame);
            this.values.set(frame, value);
        }
        return value;
    }

    set(frame, value) {
        this.values.delete(frame);
        this.values.set(frame, value);
        while (this.values.size > this.limit) this.values.delete(this.values.keys().next().value);
        return value;
    }

    clear() {
        this.values.clear();
    }
}

export class TrajectoryCache extends FrameCache {}
export class ChartCache extends FrameCache {}

export class LazyRollout {
    constructor(loader, source) {
        this.loader = loader;
        this.source = source;
        this.value = null;
    }

    async load() {
        if (!this.value) this.value = await this.loader(this.source);
        return this.value;
    }

    clear() {
        this.value = null;
    }
}

