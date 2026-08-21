import { EXPERIMENT_KINDS } from './experiment_workspace.js';

export class ExperimentWorkspacePanel {
    constructor(experimentWorkspace, { onImport = null, onChange = null, onReport = null } = {}) {
        this.experimentWorkspace = experimentWorkspace;
        this.onImport = onImport;
        this.onChange = onChange;
        this.onReport = onReport;
        this.container = null;
        this.query = '';
    }

    init(container) {
        this.container = container;
        this.render();
    }

    render() {
        if (!this.container) return;
        const root = this.container;
        root.replaceChildren();
        const heading = document.createElement('div');
        heading.className = 'panel-heading';
        heading.innerHTML = '<h2>Experiments</h2>';
        const importButton = document.createElement('button');
        importButton.type = 'button';
        importButton.textContent = 'Import rollout';
        importButton.addEventListener('click', () => this.openFilePicker());
        heading.append(importButton);
        heading.append(this.action('MD', () => this.onReport?.('markdown')));
        heading.append(this.action('CSV', () => this.onReport?.('csv')));
        heading.append(this.action('PDF', () => this.onReport?.('pdf')));
        root.append(heading);

        const controls = document.createElement('div');
        controls.className = 'experiment-controls';
        const search = document.createElement('input');
        search.type = 'search';
        search.placeholder = 'Filter experiments';
        search.value = this.query;
        search.addEventListener('input', () => {
            this.query = search.value;
            this.render();
        });
        controls.append(search);
        const kind = document.createElement('select');
        kind.innerHTML = EXPERIMENT_KINDS.map((value) => `<option value="${value}">${value}</option>`).join('');
        kind.title = 'Kind used for the next imported rollout';
        controls.append(kind);
        this.importKind = kind;
        root.append(controls);

        const list = document.createElement('div');
        list.className = 'experiment-list';
        const records = this.experimentWorkspace.experiments.list({ query: this.query }).slice(0, 100);
        records.forEach((record) => list.append(this.renderRecord(record)));
        if (!records.length) {
            const empty = document.createElement('p');
            empty.className = 'muted';
            empty.textContent = 'No experiments loaded.';
            list.append(empty);
        }
        root.append(list);
        const validation = this.experimentWorkspace.datasets.validate(this.experimentWorkspace.filteredDataset());
        const status = document.createElement('p');
        status.className = 'panel-status';
        status.textContent = `${validation.count} rollout${validation.count === 1 ? '' : 's'} | ${validation.missing.length ? 'missing data' : 'validated'}`;
        root.append(status);
    }

    renderRecord(record) {
        const item = document.createElement('article');
        item.className = `experiment-record${record.id === this.experimentWorkspace.activeExperimentId ? ' is-active' : ''}`;
        const title = document.createElement('button');
        title.type = 'button';
        title.className = 'experiment-record-title';
        title.textContent = record.name;
        title.addEventListener('click', () => {
            this.experimentWorkspace.activeExperimentId = record.id;
            this.experimentWorkspace.comparison.select([record.id]);
            this.changed();
        });
        item.append(title);
        const select = document.createElement('input');
        select.type = 'checkbox';
        select.checked = this.experimentWorkspace.comparison.selectedExperimentIds.includes(record.id);
        select.title = 'Include in comparison';
        select.addEventListener('change', () => {
            const ids = new Set(this.experimentWorkspace.comparison.selectedExperimentIds);
            if (select.checked) ids.add(record.id); else ids.delete(record.id);
            this.experimentWorkspace.comparison.select([...ids]);
            this.changed();
        });
        item.insertBefore(select, title);
        const meta = document.createElement('small');
        meta.textContent = `${record.kind}${record.folder ? ` | ${record.folder}` : ''} | ${record.rollouts.length} rollout${record.rollouts.length === 1 ? '' : 's'}`;
        item.append(meta);
        if (record.tags.length) {
            const tags = document.createElement('div');
            tags.className = 'experiment-tags';
            tags.textContent = record.tags.join(' | ');
            item.append(tags);
        }
        const actions = document.createElement('div');
        actions.className = 'experiment-actions';
        actions.append(this.action('Rename', () => {
            const name = window.prompt('Experiment name', record.name);
            if (name) { this.experimentWorkspace.experiments.rename(record.id, name); this.changed(); }
        }));
        actions.append(this.action('Clone', () => { this.experimentWorkspace.experiments.clone(record.id); this.changed(); }));
        actions.append(this.action('Delete', () => {
            if (window.confirm(`Delete ${record.name}?`)) { this.experimentWorkspace.experiments.remove(record.id); this.changed(); }
        }));
        item.append(actions);
        return item;
    }

    action(label, handler) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = label;
        button.addEventListener('click', handler);
        return button;
    }

    openFilePicker() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json,application/json';
        input.addEventListener('change', () => {
            const file = input.files?.[0];
            if (file && this.onImport) this.onImport(file, { kind: this.importKind?.value ?? 'Control' });
        });
        input.click();
    }

    changed() {
        this.render();
        if (this.onChange) this.onChange();
    }
}

export { EXPERIMENT_KINDS };
