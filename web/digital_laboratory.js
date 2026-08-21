import { ExperimentWorkspace } from './experiment_workspace.js';
import { DigitalFly } from './digital_fly.js';

export const LABORATORY_ENTITY_TYPES = Object.freeze([
    'project',
    'subject',
    'trial',
    'experiment',
    'analysisSession',
    'report',
    'export',
    'notebook',
]);

export class DigitalLaboratory {
    constructor({ experimentWorkspace = new ExperimentWorkspace(), metadata = {}, collaboration = {} } = {}) {
        this.experimentWorkspace = experimentWorkspace;
        this.pluginPlatform = experimentWorkspace.pluginPlatform ?? null;
        this.metadata = clone(metadata);
        this.collaboration = clone(collaboration);
        this.projects = new EntityStore('project');
        this.subjects = new EntityStore('subject');
        this.trials = new EntityStore('trial');
        this.experiments = new EntityStore('experiment');
        this.analysisSessions = new EntityStore('analysisSession');
        this.reports = new EntityStore('report');
        this.exports = new EntityStore('export');
        this.notebooks = new EntityStore('notebook');
        this.flies = new Map();
        this.recent = [];
    }

    createProject(options = {}) {
        return this.touch(this.projects.create({
            name: options.name ?? 'Untitled project',
            status: options.status ?? 'active',
            tags: options.tags ?? [],
            notes: options.notes ?? '',
            version: options.version ?? 1,
            metadata: options.metadata ?? {},
            subjectIds: [],
            trialIds: [],
            experimentIds: [],
            analysisSessionIds: [],
            reportIds: [],
            exportIds: [],
        }));
    }

    updateProject(id, changes = {}) {
        return this.touch(this.projects.update(id, normalizeOrganization(changes)));
    }

    addSubject({ projectId, name = 'Untitled subject', metadata = {}, tags = [], status = 'active', ...rest } = {}) {
        const project = this.projects.require(projectId);
        const subject = this.subjects.create({ projectId, name, metadata, tags, status, ...rest });
        project.subjectIds.push(subject.id);
        this.touch(project);
        return this.touch(subject);
    }

    addTrial({ projectId, subjectId = null, name = 'Untitled trial', metadata = {}, status = 'pending', ...rest } = {}) {
        const project = this.projects.require(projectId);
        if (subjectId) {
            const subject = this.subjects.require(subjectId);
            if (subject.projectId !== projectId) throw new Error('Subject does not belong to project.');
        }
        const trial = this.trials.create({ projectId, subjectId, name, metadata, status, ...rest });
        project.trialIds.push(trial.id);
        this.touch(project);
        return this.touch(trial);
    }

    addExperiment({ projectId, trialIds = [], name = 'Untitled experiment', kind = 'Control', tags = [], notes = '', version = 1, ...rest } = {}) {
        const project = this.projects.require(projectId);
        trialIds.forEach((trialId) => {
            const trial = this.trials.require(trialId);
            if (trial.projectId !== projectId) throw new Error('Trial does not belong to project.');
        });
        const experiment = this.experiments.create({ projectId, trialIds: [...trialIds], name, kind, tags, notes, version, status: 'planned', ...rest });
        project.experimentIds.push(experiment.id);
        this.touch(project);
        return this.touch(experiment);
    }

    createAnalysisSession({ experimentId, parameters = {}, featureSelection = [], statistics = {}, pluginState = {}, timeline = {}, ...rest } = {}) {
        const experiment = this.experiments.require(experimentId);
        const session = this.analysisSessions.create({
            experimentId,
            parameters: clone(parameters),
            featureSelection: [...featureSelection],
            statistics: clone(statistics),
            pluginState: clone(pluginState),
            timeline: clone(timeline),
            history: [],
            status: 'created',
            ...rest,
        });
        experiment.analysisSessionIds = experiment.analysisSessionIds ?? [];
        experiment.analysisSessionIds.push(session.id);
        this.touch(experiment);
        this.touch(session);
        return session;
    }

    recordAnalysis(sessionId, entry = {}) {
        const session = this.analysisSessions.require(sessionId);
        session.history.push({ ...clone(entry), recordedAt: new Date().toISOString() });
        session.status = entry.status ?? 'updated';
        return this.touch(session);
    }

    addReport({ experimentId, sessionId = null, format = 'markdown', content = '', attachments = [], metadata = {}, ...rest } = {}) {
        const experiment = this.experiments.require(experimentId);
        if (sessionId && this.analysisSessions.require(sessionId).experimentId !== experimentId) throw new Error('Analysis session does not belong to experiment.');
        const report = this.reports.create({ experimentId, sessionId, format, content, attachments: clone(attachments), metadata: clone(metadata), ...rest });
        experiment.reportIds = experiment.reportIds ?? [];
        experiment.reportIds.push(report.id);
        const project = this.projects.require(experiment.projectId);
        project.reportIds.push(report.id);
        this.touch(experiment);
        this.touch(project);
        return this.touch(report);
    }

    addExport({ sourceId, sourceType = 'report', format = 'json', path = '', manifest = {}, ...rest } = {}) {
        const source = this.storeFor(sourceType).require(sourceId);
        const item = this.exports.create({ sourceId, sourceType, format, path, manifest: clone(manifest), ...rest });
        const projectId = source.projectId ?? this.projectIdForSource(sourceType, source);
        if (projectId) this.projects.require(projectId).exportIds.push(item.id);
        return this.touch(item);
    }

    createNotebook({ projectId = null, title = 'Scientific notebook', markdown = '', metadata = {} } = {}) {
        if (projectId) this.projects.require(projectId);
        return this.notebooks.create({ projectId, title, markdown: String(markdown), attachments: [], metadata: clone(metadata), entries: [] });
    }

    appendNotebook(notebookId, markdown, metadata = {}) {
        const notebook = this.notebooks.require(notebookId);
        const entry = { id: makeId('entry'), markdown: String(markdown), metadata: clone(metadata), createdAt: new Date().toISOString() };
        notebook.entries.push(entry);
        notebook.markdown = notebook.entries.map((item) => item.markdown).join('\n\n');
        return this.touch(notebook);
    }

    attachNotebook(notebookId, type, id, label = '') {
        if (!['report', 'experiment', 'figure'].includes(type)) throw new Error(`Unsupported notebook attachment: ${type}`);
        if (type !== 'figure') this.storeFor(type === 'report' ? 'report' : 'experiment').require(id);
        const notebook = this.notebooks.require(notebookId);
        notebook.attachments.push({ type, id, label });
        return this.touch(notebook);
    }

    createPublicationBundle({ projectId, manuscript = null, experimentIds = [], reportIds = [], exports = [], figures = [], tables = [], supplementary = [], citation = {}, references = [] } = {}) {
        const project = this.projects.require(projectId);
        experimentIds.forEach((id) => this.experiments.require(id));
        reportIds.forEach((id) => this.reports.require(id));
        return {
            version: 1,
            projectId: project.id,
            project: { id: project.id, name: project.name, version: project.version },
            manuscript: clone(manuscript),
            experiments: [...experimentIds],
            reports: [...reportIds],
            exports: clone(exports),
            figures: clone(figures),
            tables: clone(tables),
            supplementary: clone(supplementary),
            citation: clone(citation),
            references: clone(references),
            artifactManifest: [...reportIds.map((id) => ({ type: 'report', id })), ...figures.map((path) => ({ type: 'figure', path })), ...tables.map((path) => ({ type: 'table', path }))],
            scientificScope: 'Computational publication packaging only; no new scientific claim is generated.',
        };
    }

    setCollaboration(metadata = {}) {
        this.collaboration = { ...this.collaboration, ...clone(metadata) };
        return this.collaboration;
    }

    registerFly(fly, { projectId = null, trialId = null } = {}) {
        if (!(fly instanceof DigitalFly)) throw new Error('A DigitalFly instance is required.');
        if (projectId) this.projects.require(projectId);
        if (trialId) {
            const trial = this.trials.require(trialId);
            if (projectId && trial.projectId !== projectId) throw new Error('Trial does not belong to project.');
        }
        this.flies.set(fly.id, fly);
        if (projectId) {
            const project = this.projects.require(projectId);
            project.flyIds = uniqueStrings([...(project.flyIds ?? []), fly.id]);
            this.touch(project);
        }
        if (trialId) {
            const trial = this.trials.require(trialId);
            trial.flyIds = uniqueStrings([...(trial.flyIds ?? []), fly.id]);
            this.touch(trial);
        }
        return fly;
    }

    getFly(id) { return this.flies.get(id) ?? null; }
    listFlies() { return [...this.flies.values()]; }

    dashboard() {
        return {
            projects: this.projects.size(),
            subjects: this.subjects.size(),
            trials: this.trials.size(),
            experiments: this.experiments.size(),
            analyses: this.analysisSessions.size(),
            reports: this.reports.size(),
            exports: this.exports.size(),
            flies: this.flies.size,
            plugins: this.pluginPlatform?.list?.().length ?? 0,
            notebooks: this.notebooks.size(),
        };
    }

    browse({ query = '', status = '', tag = '', sort = 'updatedAt', descending = true, groupBy = 'project', recent = false, favorite = false } = {}) {
        const projects = this.projects.list().filter((project) => {
            const haystack = `${project.name} ${project.notes} ${project.tags.join(' ')}`.toLowerCase();
            return (!query || haystack.includes(String(query).toLowerCase())) && (!status || project.status === status) && (!tag || project.tags.includes(tag)) && (!favorite || project.favorite === true);
        });
        projects.sort((a, b) => compareValues(a[sort], b[sort]) * (descending ? -1 : 1));
        const tree = projects.map((project) => ({
            ...clone(project),
            children: {
                subjects: this.subjects.list({ projectId: project.id }),
                trials: this.trials.list({ projectId: project.id }),
                experiments: this.experiments.list({ projectId: project.id }),
            },
        }));
        if (recent) return tree.filter((project) => this.recent.includes(project.id));
        return groupBy === 'project' ? tree : flattenBrowser(tree, groupBy);
    }

    search(query) {
        return this.browse({ query, descending: false });
    }

    setFavorite(projectId, favorite = true) {
        const project = this.projects.update(projectId, { favorite: Boolean(favorite) });
        return this.touch(project);
    }

    touch(entity) {
        entity.updatedAt = new Date().toISOString();
        this.recent = [entity.id, ...this.recent.filter((id) => id !== entity.id)].slice(0, 20);
        return entity;
    }

    storeFor(type) {
        const stores = { project: this.projects, subject: this.subjects, trial: this.trials, experiment: this.experiments, analysisSession: this.analysisSessions, report: this.reports, export: this.exports, notebook: this.notebooks };
        const store = stores[type];
        if (!store) throw new Error(`Unknown laboratory entity type: ${type}`);
        return store;
    }

    projectIdForSource(sourceType, source) {
        if (sourceType === 'experiment') return source.projectId;
        if (sourceType === 'report') return this.experiments.require(source.experimentId).projectId;
        return null;
    }

    toJSON() {
        return {
            version: 1,
            metadata: clone(this.metadata),
            collaboration: clone(this.collaboration),
            recent: [...this.recent],
            projects: this.projects.toJSON(),
            subjects: this.subjects.toJSON(),
            trials: this.trials.toJSON(),
            experiments: this.experiments.toJSON(),
            analysisSessions: this.analysisSessions.toJSON(),
            reports: this.reports.toJSON(),
            exports: this.exports.toJSON(),
            notebooks: this.notebooks.toJSON(),
            digitalFlies: this.listFlies().map((fly) => fly.toJSON()),
            experimentWorkspace: this.experimentWorkspace.toJSON(),
        };
    }

    restore(data = {}) {
        this.metadata = clone(data.metadata ?? {});
        this.collaboration = clone(data.collaboration ?? {});
        this.recent = [...(data.recent ?? [])];
        this.flies = new Map((data.digitalFlies ?? []).map((item) => {
            const fly = DigitalFly.fromJSON(item);
            return [fly.id, fly];
        }));
        for (const type of LABORATORY_ENTITY_TYPES) this.storeFor(type).restore(data[type === 'analysisSession' ? 'analysisSessions' : `${type}s`] ?? []);
        if (data.experimentWorkspace) this.experimentWorkspace.restore(data.experimentWorkspace);
        return this;
    }
}

export class EntityStore {
    constructor(type) {
        this.type = type;
        this.records = new Map();
    }

    create(record = {}) {
        const value = { id: makeId(this.type), type: this.type, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString(), ...clone(record) };
        this.records.set(value.id, value);
        return value;
    }

    update(id, changes = {}) {
        const record = this.require(id);
        Object.assign(record, clone(changes));
        return record;
    }

    get(id) { return this.records.get(id) ?? null; }
    require(id) { const record = this.get(id); if (!record) throw new Error(`${this.type} not found: ${id}`); return record; }
    list(filter = {}) { return [...this.records.values()].filter((record) => Object.entries(filter).every(([key, value]) => record[key] === value)).map(clone); }
    size() { return this.records.size; }
    remove(id) { return this.records.delete(id); }
    restore(records = []) { this.records = new Map(records.map((record) => [record.id, clone(record)])); return this; }
    toJSON() { return [...this.records.values()].map(clone); }
}

function normalizeOrganization(changes) {
    const result = { ...changes };
    if (result.tags !== undefined) result.tags = uniqueStrings(result.tags);
    if (result.notes !== undefined) result.notes = String(result.notes);
    if (result.version !== undefined) result.version = Number(result.version) || 1;
    return result;
}

function flattenBrowser(tree, groupBy) {
    return tree.flatMap((project) => project.children[groupBy] ?? []).map((item) => ({ ...item, projectId: item.projectId }));
}

function compareValues(left, right) {
    return String(left ?? '').localeCompare(String(right ?? ''));
}

function uniqueStrings(values = []) { return [...new Set((Array.isArray(values) ? values : [values]).filter(Boolean).map(String))]; }
function makeId(prefix) { return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`; }
function clone(value) { return value === undefined ? undefined : JSON.parse(JSON.stringify(value)); }
