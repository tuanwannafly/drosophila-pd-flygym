export const PLUGIN_HOOKS = Object.freeze([
    'onImport',
    'onValidation',
    'onNormalization',
    'onQC',
    'onFeatureExtraction',
    'onAnalysis',
    'onStatistics',
    'onComparison',
    'onVisualization',
    'onReport',
    'onExport',
    'onWorkspaceLoaded',
]);

export const PLUGIN_CAPABILITIES = Object.freeze([
    'analysis',
    'statistics',
    'visualization',
    'report',
    'export',
    'comparison',
    'toolbar',
    'viewer',
]);

export class PluginManifestError extends Error {
    constructor(message, details = {}) {
        super(message);
        this.name = 'PluginManifestError';
        this.details = details;
    }
}

/**
 * The only object supplied to plugin code. The host may expose narrow,
 * read-only services through `services`; the internal Workspace is never
 * placed on this context.
 */
export class PluginContext {
    constructor(manifest, services = {}) {
        if (Object.prototype.hasOwnProperty.call(services, 'workspace')) {
            throw new PluginManifestError('Plugin context cannot expose the internal Workspace.');
        }
        this.plugin = Object.freeze({
            id: manifest.id,
            name: manifest.name,
            version: manifest.version,
            capabilities: [...manifest.capabilities],
        });
        this.services = Object.freeze({ ...services });
    }

    get(name) {
        return this.services[name];
    }

    getState() {
        const provider = this.services.getState;
        return typeof provider === 'function' ? provider() : undefined;
    }
}

export class PluginPlatform {
    constructor(options = {}) {
        this.plugins = new Map();
        this.contextProvider = options.contextProvider ?? (() => ({}));
        this.logger = options.logger ?? null;
        this.loader = new PluginLoader(this);
    }

    register(definition) {
        const normalized = validatePluginDefinition(definition);
        if (this.plugins.has(normalized.manifest.id)) {
            throw new PluginManifestError(`Plugin already registered: ${normalized.manifest.id}`);
        }
        this.plugins.set(normalized.manifest.id, {
            definition: normalized,
            enabled: false,
            loaded: false,
            cleanup: null,
        });
        return this.describe(normalized.manifest.id);
    }

    unregister(id) {
        if (!this.plugins.has(id)) return false;
        this.unload(id);
        return this.plugins.delete(id);
    }

    enable(id) {
        return this._load(id, new Set());
    }

    disable(id) {
        const record = this.require(id);
        this.deactivate(record);
        return this.describe(id);
    }

    reload(id) {
        this.unload(id);
        return this.enable(id);
    }

    unload(id) {
        const record = this.require(id);
        this.deactivate(record);
        return this.describe(id);
    }

    list(capability = null) {
        return [...this.plugins.keys()]
            .map((id) => this.describe(id))
            .filter((plugin) => capability === null || plugin.manifest.capabilities.includes(capability));
    }

    run(id, input, metadata = {}) {
        const record = this.require(id);
        if (!record.enabled) throw new Error(`Plugin is disabled: ${id}`);
        if (typeof record.definition.run !== 'function') {
            throw new Error(`Plugin does not expose run(): ${id}`);
        }
        return record.definition.run(input, this.context(record, metadata));
    }

    emit(hook, payload, metadata = {}) {
        if (!PLUGIN_HOOKS.includes(hook)) throw new Error(`Unknown plugin hook: ${hook}`);
        return this.list()
            .filter((plugin) => plugin.enabled && typeof this.plugins.get(plugin.manifest.id).definition.hooks[hook] === 'function')
            .map((plugin) => {
                const record = this.plugins.get(plugin.manifest.id);
                const value = record.definition.hooks[hook](payload, this.context(record, metadata));
                return { pluginId: plugin.manifest.id, value };
            });
    }

    validate(definition) {
        return validatePluginDefinition(definition);
    }

    describe(id) {
        const record = this.require(id);
        return {
            manifest: { ...record.definition.manifest, dependencies: [...record.definition.manifest.dependencies], capabilities: [...record.definition.manifest.capabilities] },
            enabled: record.enabled,
            loaded: record.loaded,
        };
    }

    _load(id, loading) {
        const record = this.require(id);
        if (record.enabled) return this.describe(id);
        if (loading.has(id)) throw new PluginManifestError(`Circular plugin dependency: ${id}`);
        loading.add(id);
        record.definition.manifest.dependencies.forEach((dependency) => this._load(dependency, loading));
        loading.delete(id);
        const context = this.context(record);
        if (typeof record.definition.activate === 'function') {
            const cleanup = record.definition.activate(context);
            record.cleanup = typeof cleanup === 'function' ? cleanup : null;
        }
        record.loaded = true;
        record.enabled = true;
        this.log('enable', record.definition.manifest.id);
        return this.describe(id);
    }

    deactivate(record) {
        if (!record.loaded) return;
        if (typeof record.definition.deactivate === 'function') {
            record.definition.deactivate(this.context(record));
        }
        if (record.cleanup) record.cleanup();
        record.cleanup = null;
        record.loaded = false;
        record.enabled = false;
        this.log('disable', record.definition.manifest.id);
    }

    context(record, metadata = {}) {
        const services = this.contextProvider({ manifest: record.definition.manifest, metadata }) ?? {};
        return new PluginContext(record.definition.manifest, services);
    }

    require(id) {
        const record = this.plugins.get(id);
        if (!record) throw new Error(`Plugin not found: ${id}`);
        return record;
    }

    log(event, id) {
        if (typeof this.logger === 'function') this.logger({ event, id });
    }
}

export class PluginLoader {
    constructor(platform) {
        this.platform = platform;
    }

    validate(definition) {
        return this.platform.validate(definition);
    }

    load(definitionOrId) {
        const id = typeof definitionOrId === 'string'
            ? definitionOrId
            : this.platform.register(definitionOrId).manifest.id;
        return this.platform.enable(id);
    }

    unload(id) {
        return this.platform.unload(id);
    }

    reload(id) {
        return this.platform.reload(id);
    }
}

function validatePluginDefinition(definition) {
    if (!definition || typeof definition !== 'object') {
        throw new PluginManifestError('Plugin definition must be an object.');
    }
    const manifest = definition.manifest;
    if (!manifest || typeof manifest !== 'object') {
        throw new PluginManifestError('Plugin manifest is required.');
    }
    ['id', 'name', 'version', 'author', 'description'].forEach((field) => {
        if (typeof manifest[field] !== 'string' || manifest[field].trim() === '') {
            throw new PluginManifestError(`Manifest field is required: ${field}`, { field });
        }
    });
    const dependencies = manifest.dependencies ?? [];
    const capabilities = manifest.capabilities ?? [];
    if (!Array.isArray(dependencies) || dependencies.some((value) => typeof value !== 'string' || value.trim() === '')) {
        throw new PluginManifestError('Manifest dependencies must be an array of plugin ids.');
    }
    if (!Array.isArray(capabilities) || capabilities.some((value) => !PLUGIN_CAPABILITIES.includes(value))) {
        throw new PluginManifestError('Manifest capabilities contain an unsupported value.');
    }
    const hooks = definition.hooks ?? {};
    if (Object.keys(hooks).some((hook) => !PLUGIN_HOOKS.includes(hook) || typeof hooks[hook] !== 'function')) {
        throw new PluginManifestError('Plugin hooks must use known hook names and functions.');
    }
    return {
        ...definition,
        manifest: {
            ...manifest,
            dependencies: [...dependencies],
            capabilities: [...capabilities],
        },
        hooks,
    };
}
