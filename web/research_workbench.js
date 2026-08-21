// Management-only workbench state. It stores references and user notes; it does
// not run simulations or manufacture scientific observations.

export const WORKBENCH_TABS = Object.freeze([
    'dashboard', 'comparison', 'validation', 'figures', 'notebook', 'bundle', 'layout',
]);

export const DEFAULT_WORKBENCH_LAYOUTS = Object.freeze({
    Analysis: Object.freeze({ panels: ['research-workbench', 'experiment-manager', 'scene', 'inspector', 'timeline'], dock: 'left', splitView: false, sizes: {}, floating: [], fullscreen: null }),
    Publication: Object.freeze({ panels: ['research-workbench', 'scene', 'timeline'], dock: 'bottom', splitView: true, sizes: {}, floating: [], fullscreen: null }),
    Comparison: Object.freeze({ panels: ['research-workbench', 'comparison-viewer', 'scene', 'timeline'], dock: 'right', splitView: true, sizes: {}, floating: [], fullscreen: null }),
    Validation: Object.freeze({ panels: ['research-workbench', 'experiment-dashboard', 'scene'], dock: 'bottom', splitView: false, sizes: {}, floating: [], fullscreen: null }),
});

export class WorkbenchLayoutManager {
    constructor(layouts = DEFAULT_WORKBENCH_LAYOUTS) {
        this.layouts = new Map(Object.entries(clone(layouts)));
        this.currentName = 'Analysis';
        this.current = clone(this.layouts.get(this.currentName));
    }

    names() { return [...this.layouts.keys()]; }

    setLayout(layout = {}, name = this.currentName) {
        this.currentName = name;
        this.current = normalizeLayout(layout);
        return this.current;
    }

    save(name = this.currentName) {
        this.layouts.set(String(name), clone(this.current));
        this.currentName = String(name);
        return this.current;
    }

    load(name) {
        if (!this.layouts.has(name)) return null;
        this.currentName = name;
        this.current = clone(this.layouts.get(name));
        return this.current;
    }

    reset() {
        return this.load('Analysis') ?? this.setLayout(DEFAULT_WORKBENCH_LAYOUTS.Analysis, 'Analysis');
    }

    resize(panel, size) {
        if (!panel) return this.current;
        this.current.sizes[panel] = Math.max(120, Math.round(Number(size) || 0));
        return this.current;
    }

    setFloating(panel, floating = true) {
        const values = new Set(this.current.floating);
        if (floating) values.add(panel); else values.delete(panel);
        this.current.floating = [...values];
        return this.current;
    }

    setFullscreen(panel = null) {
        this.current.fullscreen = panel;
        return this.current;
    }

    snapshot() {
        return { currentName: this.currentName, current: clone(this.current), layouts: Object.fromEntries(this.layouts) };
    }

    restore(snapshot = {}) {
        if (snapshot.layouts && typeof snapshot.layouts === 'object') this.layouts = new Map(Object.entries(clone(snapshot.layouts)));
        this.currentName = snapshot.currentName ?? this.currentName;
        this.current = normalizeLayout(snapshot.current ?? this.layouts.get(this.currentName) ?? DEFAULT_WORKBENCH_LAYOUTS.Analysis);
        return this.current;
    }
}

export class ResearchNotebook {
    constructor(entries = []) {
        this.entries = Array.isArray(entries) ? entries.map(clone) : [];
    }

    add(type, content = '', metadata = {}) {
        const entry = {
            id: `notebook-entry-${Date.now().toString(36)}-${this.entries.length}`,
            type: String(type),
            content: String(content),
            metadata: clone(metadata),
            timestamp: new Date().toISOString(),
            linkedRollout: metadata.linkedRollout ?? null,
        };
        this.entries.push(entry);
        return entry;
    }

    addMarkdown(content, metadata) { return this.add('markdown', content, metadata); }
    addObservation(content, metadata) { return this.add('observation', content, metadata); }
    addConclusion(content, metadata) { return this.add('conclusion', content, metadata); }
    addReference(content, metadata) { return this.add('reference', content, metadata); }
    addImage(path, metadata) { return this.add('image', path, metadata); }
    addChart(path, metadata) { return this.add('chart', path, metadata); }

    list() { return this.entries.map(clone); }
    clear() { this.entries = []; }
}

export class FigureBuilder {
    constructor(figures = []) { this.figures = Array.isArray(figures) ? figures.map(clone) : []; }

    create({ title = 'Untitled figure', caption = '', format = 'png' } = {}) {
        const figure = {
            id: `figure-${Date.now().toString(36)}-${this.figures.length}`,
            title: String(title),
            caption: String(caption),
            format: String(format),
            subplots: [],
            legend: { visible: true, entries: [] },
            scaleBar: null,
            sourceReferences: [],
            createdAt: new Date().toISOString(),
            scientificScope: 'Figure composition of existing computational artifacts only.',
        };
        this.figures.push(figure);
        return figure;
    }

    addSubplot(figure, subplot = {}) {
        const target = this.require(figure);
        target.subplots.push({ ...clone(subplot), id: subplot.id ?? `subplot-${target.subplots.length}` });
        return target;
    }

    setLegend(figure, legend = {}) { const target = this.require(figure); target.legend = { ...target.legend, ...clone(legend) }; return target; }
    setScaleBar(figure, scaleBar = null) { const target = this.require(figure); target.scaleBar = clone(scaleBar); return target; }
    setCaption(figure, caption) { const target = this.require(figure); target.caption = String(caption ?? ''); return target; }
    addSourceReference(figure, reference) { const target = this.require(figure); target.sourceReferences.push(String(reference)); return target; }
    require(figure) { const id = typeof figure === 'string' ? figure : figure?.id; const found = this.figures.find((item) => item.id === id); if (!found) throw new Error(`Figure not found: ${id}`); return found; }
    list() { return this.figures.map(clone); }
}

export class ValidationCenter {
    constructor() { this.report = null; }

    attach(report) { this.report = clone(report); return this.report; }

    summarize() {
        const report = this.report ?? {};
        return {
            available: Boolean(this.report),
            status: report.overall_pass === true ? 'PASS' : this.report ? 'REVIEW' : 'NOT_AVAILABLE',
            rmse: report.rmse ?? null,
            mae: report.mae ?? null,
            r2: report.r2 ?? null,
            correlation: report.correlation ?? null,
            bootstrap: report.bootstrap ?? null,
            crossValidation: report.cross_validation ?? report.crossValidation ?? null,
            effectSize: report.effect_size ?? report.effectSize ?? null,
            outliers: report.outliers ?? null,
            missingValues: report.missing_values ?? report.missingValues ?? null,
            warnings: Array.isArray(report.warnings) ? report.warnings : [],
            scope: 'Validation references existing computational reports only; no new statistical or biological claim is generated.',
        };
    }
}

export class ProjectBundleManager {
    build({ metadata = {}, analysis = null, charts = [], validation = null, reports = [], notebook = [], publication = [], artifacts = [] } = {}) {
        const bundle = {
            version: 1,
            type: 'research-bundle',
            createdAt: new Date().toISOString(),
            metadata: clone(metadata),
            datasetMetadata: clone(metadata.dataset ?? {}),
            analysis: clone(analysis),
            charts: clone(charts),
            validation: clone(validation),
            reports: clone(reports),
            notebook: clone(notebook),
            publicationAssets: clone(publication),
            artifacts: clone(artifacts),
            scientificScope: 'Management bundle for imported computational outputs; it does not create rollout data or scientific claims.',
        };
        bundle.manifest = buildManifest(bundle);
        bundle.checksum = checksum(stableStringify(bundle.manifest));
        return bundle;
    }

    download(bundle, filename = 'fly-studio-research-bundle.json') {
        if (typeof document === 'undefined') return false;
        const link = document.createElement('a');
        link.href = URL.createObjectURL(new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' }));
        link.download = filename;
        link.click();
        URL.revokeObjectURL(link.href);
        return true;
    }
}

export class ResearchWorkbench {
    constructor({ workspace, experimentWorkspace, laboratory, analyticsDashboard, viewportRenderer = null } = {}) {
        this.workspace = workspace;
        this.experimentWorkspace = experimentWorkspace;
        this.laboratory = laboratory;
        this.analyticsDashboard = analyticsDashboard;
        this.viewportRenderer = viewportRenderer;
        this.layout = new WorkbenchLayoutManager();
        this.notebook = new ResearchNotebook();
        this.figures = new FigureBuilder();
        this.validation = new ValidationCenter();
        this.bundles = new ProjectBundleManager();
        this.activeTab = 'dashboard';
    }

    dashboard() {
        const report = this.analyticsDashboard?.lastReport ?? this.analyticsDashboard?.compute?.() ?? null;
        const lab = this.laboratory?.dashboard?.() ?? {};
        const validation = this.validation.summarize();
        return {
            datasets: this.experimentWorkspace?.datasets?.list?.().length ?? 0,
            experiments: this.experimentWorkspace?.experiments?.list?.().length ?? 0,
            rollouts: this.experimentWorkspace?.datasets?.list?.().length ?? 0,
            selectedFly: this.laboratory?.listFlies?.()[0]?.name ?? null,
            playbackStatus: this.workspace?.playbackState ?? 'Stopped',
            currentFrame: this.workspace?.currentFrame ?? 0,
            totalFrames: this.workspace?.totalFrames ?? 1,
            currentBehavior: this.currentBehavior(),
            currentStatistics: this.workspace?.rolloutStatistics?.summary ?? null,
            validationStatus: validation.status,
            computationalIndex: this.workspace?.rolloutStatistics?.computationalIndex ?? null,
            analytics: report,
            laboratory: lab,
            scientificScope: 'Computational workbench only; no biological interpretation is implied.',
        };
    }

    currentBehavior() {
        const frame = Number(this.workspace?.currentFrame ?? 0);
        return (this.workspace?.rollout?.behaviors ?? []).find((item) => frame >= item.startFrame && frame <= item.endFrame)?.label ?? null;
    }

    bundle() {
        return this.bundles.build({
            metadata: { activeTab: this.activeTab, layout: this.layout.snapshot(), currentFrame: this.workspace?.currentFrame ?? 0 },
            analysis: this.analyticsDashboard?.lastReport ?? null,
            validation: this.validation.report,
            reports: this.laboratory?.reports?.list?.() ?? [],
            notebook: this.notebook.list(),
            publication: this.figures.list(),
            artifacts: this.experimentWorkspace?.datasets?.list?.().map((entry) => ({ id: entry.id, fingerprint: entry.fingerprint })) ?? [],
        });
    }

    snapshot() {
        return { activeTab: this.activeTab, layout: this.layout.snapshot(), notebook: this.notebook.list(), figures: this.figures.list(), validation: clone(this.validation.report) };
    }

    restore(snapshot = {}) {
        this.activeTab = WORKBENCH_TABS.includes(snapshot.activeTab) ? snapshot.activeTab : 'dashboard';
        this.layout.restore(snapshot.layout);
        this.notebook = new ResearchNotebook(snapshot.notebook);
        this.figures = new FigureBuilder(snapshot.figures);
        this.validation.attach(snapshot.validation);
        return this;
    }
}

function normalizeLayout(layout = {}) {
    return {
        panels: Array.isArray(layout.panels) ? [...new Set(layout.panels.map(String))] : [],
        dock: String(layout.dock ?? 'left'),
        splitView: Boolean(layout.splitView),
        sizes: clone(layout.sizes ?? {}),
        floating: Array.isArray(layout.floating) ? [...new Set(layout.floating.map(String))] : [],
        fullscreen: layout.fullscreen ?? null,
    };
}

function buildManifest(bundle) {
    return {
        version: 1,
        type: bundle.type,
        createdAt: bundle.createdAt,
        sections: ['datasetMetadata', 'analysis', 'charts', 'validation', 'reports', 'notebook', 'publicationAssets', 'artifacts'],
        artifactCount: Array.isArray(bundle.artifacts) ? bundle.artifacts.length : 0,
        scientificScope: bundle.scientificScope,
    };
}

function stableStringify(value) {
    if (value === null || typeof value !== 'object') return JSON.stringify(value);
    if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
    return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`).join(',')}}`;
}

function checksum(value) {
    let result = 2166136261;
    for (let index = 0; index < value.length; index += 1) {
        result ^= value.charCodeAt(index);
        result = Math.imul(result, 16777619);
    }
    return `fnv1a-${(result >>> 0).toString(16)}`;
}

function clone(value) {
    if (value === undefined) return undefined;
    return JSON.parse(JSON.stringify(value));
}
