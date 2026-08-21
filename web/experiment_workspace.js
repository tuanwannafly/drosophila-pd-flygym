import { PluginPlatform } from './plugin_platform.js';

const MAX_RECENT_ITEMS = 20;

export const EXPERIMENT_KINDS = Object.freeze([
    'Healthy',
    'PD',
    'Candidate',
    'Control',
]);

export class ExperimentManager {
    constructor(records = []) {
        this.records = new Map();
        records.forEach((record) => this.importRecord(record));
    }

    create({ name = 'Untitled experiment', kind = 'Control', folder = '', tags = [], notes = '', metadata = {}, rollouts = [] } = {}) {
        const record = {
            id: createId('experiment'),
            name: String(name),
            kind: EXPERIMENT_KINDS.includes(kind) ? kind : 'Control',
            folder: String(folder ?? ''),
            tags: uniqueStrings(tags),
            notes: String(notes ?? ''),
            metadata: clone(metadata),
            rollouts: [...rollouts],
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        };
        this.records.set(record.id, record);
        return record;
    }

    importRecord(record) {
        if (!record || typeof record !== 'object') throw new Error('Invalid experiment record.');
        const imported = {
            ...record,
            id: String(record.id ?? createId('experiment')),
            name: String(record.name ?? 'Untitled experiment'),
            kind: EXPERIMENT_KINDS.includes(record.kind) ? record.kind : 'Control',
            folder: String(record.folder ?? ''),
            tags: uniqueStrings(record.tags),
            notes: String(record.notes ?? ''),
            metadata: clone(record.metadata ?? {}),
            rollouts: Array.isArray(record.rollouts) ? record.rollouts : [],
            createdAt: record.createdAt ?? new Date().toISOString(),
            updatedAt: record.updatedAt ?? new Date().toISOString(),
        };
        this.records.set(imported.id, imported);
        return imported;
    }

    importRollout(rollout, options = {}) {
        if (!rollout || typeof rollout !== 'object') throw new Error('A normalized rollout is required.');
        const record = this.create({
            name: options.name ?? rollout.source?.name ?? 'FlyGym experiment',
            kind: options.kind ?? 'Control',
            folder: options.folder,
            tags: options.tags,
            notes: options.notes,
            metadata: { ...rollout.metadata, ...(options.metadata ?? {}) },
            rollouts: [{ id: createId('rollout'), rollout, metadata: options.rolloutMetadata ?? {} }],
        });
        return record;
    }

    get(id) {
        return this.records.get(id) ?? null;
    }

    list(filter = {}) {
        return [...this.records.values()].filter((record) => matchesExperiment(record, filter));
    }

    folders() {
        return uniqueStrings([...this.records.values()].map((record) => record.folder).filter(Boolean)).sort();
    }

    rename(id, name) {
        const record = this.require(id);
        record.name = String(name).trim() || record.name;
        touch(record);
        return record;
    }

    clone(id, overrides = {}) {
        const source = this.require(id);
        return this.importRecord({
            ...clone(source),
            ...overrides,
            id: createId('experiment'),
            name: overrides.name ?? `${source.name} Copy`,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
        });
    }

    remove(id) {
        return this.records.delete(id);
    }

    updateOrganization(id, { folder, tags, notes } = {}) {
        const record = this.require(id);
        if (folder !== undefined) record.folder = String(folder);
        if (tags !== undefined) record.tags = uniqueStrings(tags);
        if (notes !== undefined) record.notes = String(notes);
        touch(record);
        return record;
    }

    addRollout(id, rollout, metadata = {}) {
        const record = this.require(id);
        const item = { id: createId('rollout'), rollout, metadata: clone(metadata) };
        record.rollouts.push(item);
        touch(record);
        return item;
    }

    require(id) {
        const record = this.get(id);
        if (!record) throw new Error(`Experiment not found: ${id}`);
        return record;
    }

    toJSON() {
        return [...this.records.values()].map(clone);
    }
}

export class DatasetManager {
    constructor(entries = []) {
        this.entries = new Map();
        this.recent = [];
        entries.forEach((entry) => this.add(entry.rollout, entry));
    }

    add(rollout, { experimentId = null, metadata = {}, id = null } = {}) {
        if (!rollout || typeof rollout !== 'object') throw new Error('A normalized rollout is required.');
        const fingerprint = fingerprintRollout(rollout);
        const duplicate = [...this.entries.values()].find((entry) => entry.fingerprint === fingerprint);
        if (duplicate) return { entry: duplicate, duplicate: true };
        const entry = {
            id: id ?? createId('dataset-row'),
            experimentId,
            rollout,
            metadata: clone(metadata),
            fingerprint,
            addedAt: new Date().toISOString(),
        };
        this.entries.set(entry.id, entry);
        this.recent = [entry.id, ...this.recent.filter((value) => value !== entry.id)].slice(0, MAX_RECENT_ITEMS);
        return { entry, duplicate: false };
    }

    addBatch(items = []) {
        return items.map((item) => this.add(item.rollout ?? item, item.options ?? item.metadata ?? {}));
    }

    get(id) {
        return this.entries.get(id) ?? null;
    }

    list(filter = {}) {
        return [...this.entries.values()].filter((entry) => matchesRollout(entry, filter));
    }

    validate(entries = this.list()) {
        const missing = entries.filter((entry) => !entry.rollout || !entry.rollout.frameCount);
        const fingerprints = new Set();
        const duplicates = [];
        entries.forEach((entry) => {
            if (fingerprints.has(entry.fingerprint)) duplicates.push(entry.id);
            fingerprints.add(entry.fingerprint);
        });
        return {
            valid: missing.length === 0,
            count: entries.length,
            missing: missing.map((entry) => entry.id),
            duplicates,
            compatible: entries.every((entry) => String(entry.rollout?.source?.format?.format ?? entry.rollout?.source?.format ?? '').startsWith('flygym')),
            unsupportedFormats: uniqueStrings(entries
                .map((entry) => entry.rollout?.source?.format?.format ?? entry.rollout?.source?.format)
                .filter((format) => format && !String(format).startsWith('flygym'))),
            channels: uniqueStrings(entries.flatMap((entry) => Object.keys(entry.rollout?.channels ?? {}))),
        };
    }

    remove(id) {
        this.recent = this.recent.filter((value) => value !== id);
        return this.entries.delete(id);
    }

    toJSON() {
        return [...this.entries.values()].map(clone);
    }
}

export class ComparisonWorkspace {
    constructor() {
        this.selectedExperimentIds = [];
        this.alignment = { mode: 'frame', anchor: 0 };
        this.synchronized = true;
        this.syncCamera = true;
        this.syncSelection = true;
        this.syncTimeline = true;
        this.syncOverlays = true;
        this.currentFrame = 0;
    }

    select(ids) {
        this.selectedExperimentIds = uniqueStrings(ids).slice(0, 8);
        return this.selectedExperimentIds;
    }

    setAlignment(alignment = {}) {
        this.alignment = { ...this.alignment, ...alignment };
        return this.alignment;
    }

    setSynchronized(value) {
        this.synchronized = Boolean(value);
        return this.synchronized;
    }

    setSynchronization(options = {}) {
        ['syncCamera', 'syncSelection', 'syncTimeline', 'syncOverlays'].forEach((key) => {
            if (options[key] !== undefined) this[key] = Boolean(options[key]);
        });
        return this.snapshot();
    }

    setFrame(frame) {
        this.currentFrame = Math.max(0, Math.round(Number(frame) || 0));
        return this.currentFrame;
    }

    snapshot() {
        return {
            selectedExperimentIds: [...this.selectedExperimentIds],
            alignment: clone(this.alignment),
            synchronized: this.synchronized,
            syncCamera: this.syncCamera,
            syncSelection: this.syncSelection,
            syncTimeline: this.syncTimeline,
            syncOverlays: this.syncOverlays,
            currentFrame: this.currentFrame,
        };
    }
}

export class SnapshotStore {
    constructor(limit = 20) {
        this.limit = Math.max(1, limit);
        this.snapshots = [];
    }

    save(state, name = 'Workspace snapshot') {
        const snapshot = {
            id: createId('snapshot'),
            name,
            createdAt: new Date().toISOString(),
            state: clone(state),
        };
        this.snapshots = [snapshot, ...this.snapshots].slice(0, this.limit);
        return snapshot;
    }

    get(id) {
        return this.snapshots.find((snapshot) => snapshot.id === id) ?? null;
    }

    list() {
        return this.snapshots.map(clone);
    }

    remove(id) {
        this.snapshots = this.snapshots.filter((snapshot) => snapshot.id !== id);
    }
}

export class LayoutManager {
    constructor() {
        this.layout = {
            panels: ['experiment-manager', 'scene', 'inspector', 'timeline', 'dashboard'],
            splitView: false,
            dock: 'left',
        };
    }

    setLayout(layout = {}) {
        this.layout = { ...this.layout, ...clone(layout) };
        return this.layout;
    }

    togglePanel(panel, visible = true) {
        const panels = new Set(this.layout.panels);
        if (visible) panels.add(panel); else panels.delete(panel);
        this.layout.panels = [...panels];
        return this.layout;
    }

    snapshot() {
        return clone(this.layout);
    }
}

export class PluginRegistry {
    constructor() {
        this.plugins = new Map();
    }

    register(plugin) {
        if (!plugin?.id || typeof plugin.run !== 'function') {
            throw new Error('Plugin requires an id and run function.');
        }
        this.plugins.set(plugin.id, { ...plugin });
        return plugin;
    }

    unregister(id) {
        return this.plugins.delete(id);
    }

    list(type = null) {
        return [...this.plugins.values()]
            .filter((plugin) => type === null || plugin.type === type)
            .map(({ run, ...metadata }) => metadata);
    }

    run(id, input, context = {}) {
        const plugin = this.plugins.get(id);
        if (!plugin) throw new Error(`Plugin not found: ${id}`);
        return plugin.run(input, context);
    }
}

export class ExperimentWorkspace {
    constructor({ experiments = [], datasets = [] } = {}) {
        this.experiments = new ExperimentManager(experiments);
        this.datasets = new DatasetManager(datasets);
        this.comparison = new ComparisonWorkspace();
        this.snapshots = new SnapshotStore();
        this.layout = new LayoutManager();
        this.plugins = new PluginRegistry();
        // Keep the original registry API and expose the additive manifest-based platform separately.
        this.pluginPlatform = new PluginPlatform();
        this.filters = { behavior: '', animal: '', minTime: null, maxTime: null, minVelocity: null, maxVelocity: null, minEnergy: null, maxEnergy: null, minStride: null, maxStride: null, custom: null };
        this.activeExperimentId = null;
    }

    importRollout(rollout, options = {}) {
        const experiment = this.experiments.importRollout(rollout, options);
        this.datasets.add(rollout, { experimentId: experiment.id, metadata: options.metadata });
        this.activeExperimentId = experiment.id;
        return experiment;
    }

    setFilter(filter = {}) {
        this.filters = { ...this.filters, ...filter };
        return this.filters;
    }

    filteredDataset() {
        return this.datasets.list(this.filters);
    }

    saveSnapshot(name, context = {}) {
        return this.snapshots.save(this.snapshot(context), name);
    }

    restoreSnapshot(id) {
        const snapshot = this.snapshots.get(id);
        if (!snapshot) return null;
        this.activeExperimentId = snapshot.state.activeExperimentId;
        this.filters = clone(snapshot.state.filters);
        this.comparison = Object.assign(new ComparisonWorkspace(), snapshot.state.comparison);
        this.layout.setLayout(snapshot.state.layout);
        return snapshot.state;
    }

    restore(data = {}) {
        this.experiments = new ExperimentManager(data.experiments ?? []);
        this.datasets = new DatasetManager(data.datasets ?? []);
        if (data.state) {
            this.activeExperimentId = data.state.activeExperimentId ?? null;
            this.filters = { ...this.filters, ...(data.state.filters ?? {}) };
            this.comparison = Object.assign(new ComparisonWorkspace(), data.state.comparison ?? {});
            this.layout.setLayout(data.state.layout ?? {});
        }
        this.snapshots.snapshots = Array.isArray(data.snapshots) ? data.snapshots.map(clone) : [];
        return this;
    }

    snapshot(context = {}) {
        return {
            activeExperimentId: this.activeExperimentId,
            filters: clone(this.filters),
            comparison: this.comparison.snapshot(),
            layout: this.layout.snapshot(),
            camera: clone(context.camera ?? null),
            timeline: clone(context.timeline ?? null),
            selection: clone(context.selection ?? null),
            workspace: clone(context.workspace ?? null),
            statistics: clone(context.statistics ?? null),
        };
    }

    toJSON() {
        return {
            version: 1,
            experiments: this.experiments.toJSON(),
            datasets: this.datasets.toJSON(),
            state: this.snapshot(),
            snapshots: this.snapshots.list(),
        };
    }
}

function matchesExperiment(record, filter) {
    if (filter.kind && record.kind !== filter.kind) return false;
    if (filter.folder && record.folder !== filter.folder) return false;
    if (filter.tag && !record.tags.includes(filter.tag)) return false;
    if (filter.query) {
        const haystack = `${record.name} ${record.kind} ${record.folder} ${record.tags.join(' ')} ${record.notes}`.toLowerCase();
        if (!haystack.includes(String(filter.query).toLowerCase())) return false;
    }
    return true;
}

function matchesRollout(entry, filter) {
    const rollout = entry.rollout;
    if (!rollout) return false;
    if (filter.experimentId && entry.experimentId !== filter.experimentId) return false;
    if (filter.behavior) {
        const behaviors = rollout.behaviors ?? [];
        if (!behaviors.some((behavior) => `${behavior.label} ${behavior.type}`.toLowerCase().includes(String(filter.behavior).toLowerCase()))) return false;
    }
    if (filter.animal && String(rollout.metadata?.animal_id ?? '').toLowerCase() !== String(filter.animal).toLowerCase()) return false;
    if (!within(rollout.statistics?.summary?.speed?.mean, filter.minVelocity, filter.maxVelocity)) return false;
    if (!within(rollout.statistics?.summary?.energy, filter.minEnergy, filter.maxEnergy)) return false;
    if (!within(rollout.statistics?.summary?.strideFrequency, filter.minStride, filter.maxStride)) return false;
    if (filter.minTime !== null && Number(rollout.durationS ?? 0) < Number(filter.minTime)) return false;
    if (filter.maxTime !== null && Number(rollout.durationS ?? 0) > Number(filter.maxTime)) return false;
    if (typeof filter.custom === 'function' && !filter.custom(entry)) return false;
    return true;
}

function within(value, minimum, maximum) {
    if (minimum === null || minimum === undefined) return true;
    if (!Number.isFinite(Number(value)) || Number(value) < Number(minimum)) return false;
    if (maximum === null || maximum === undefined) return true;
    return Number(value) <= Number(maximum);
}

function fingerprintRollout(rollout) {
    const basis = {
        source: rollout.source,
        metadata: rollout.metadata,
        frameCount: rollout.frameCount,
        timestepS: rollout.timestepS,
        channels: Object.fromEntries(Object.entries(rollout.channels ?? {}).map(([name, series]) => [
            name,
            Array.isArray(series) ? series.slice(0, 3).concat(series.slice(-3)) : Object.keys(series ?? {}),
        ])),
    };
    return hash(stableStringify(basis));
}

function stableStringify(value) {
    if (value === null || typeof value !== 'object') return JSON.stringify(value);
    if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
}

function hash(value) {
    let result = 2166136261;
    for (let index = 0; index < value.length; index += 1) {
        result ^= value.charCodeAt(index);
        result = Math.imul(result, 16777619);
    }
    return `fnv1a-${(result >>> 0).toString(16)}`;
}

function uniqueStrings(values = []) {
    return [...new Set((Array.isArray(values) ? values : [values]).filter((value) => value !== null && value !== undefined).map(String))];
}

function clone(value) {
    if (value === undefined) return undefined;
    return JSON.parse(JSON.stringify(value));
}

function createId(prefix) {
    return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function touch(record) {
    record.updatedAt = new Date().toISOString();
}
