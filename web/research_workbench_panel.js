export class ResearchWorkbenchPanel {
    constructor(workbench, { onChange = null } = {}) {
        this.workbench = workbench;
        this.onChange = onChange;
        this.container = null;
    }

    init(container) {
        this.container = container;
        this.render();
    }

    render() {
        if (!this.container) return;
        this.container.replaceChildren();
        this.container.className = 'research-workbench';
        const header = document.createElement('div');
        header.className = 'panel-heading research-workbench-heading';
        header.innerHTML = '<h2>Research Workbench</h2><span class="panel-status">Imported computational data only</span>';
        this.container.append(header);

        const tabs = document.createElement('nav');
        tabs.className = 'research-workbench-tabs';
        ['dashboard', 'comparison', 'validation', 'figures', 'notebook', 'bundle', 'layout'].forEach((tab) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = tab[0].toUpperCase() + tab.slice(1);
            button.className = this.workbench.activeTab === tab ? 'is-active' : '';
            button.addEventListener('click', () => { this.workbench.activeTab = tab; this.render(); });
            tabs.append(button);
        });
        this.container.append(tabs);

        const content = document.createElement('section');
        content.className = 'research-workbench-content';
        this.container.append(content);
        const renderers = {
            dashboard: () => this.renderDashboard(content),
            comparison: () => this.renderComparison(content),
            validation: () => this.renderValidation(content),
            figures: () => this.renderFigures(content),
            notebook: () => this.renderNotebook(content),
            bundle: () => this.renderBundle(content),
            layout: () => this.renderLayout(content),
        };
        (renderers[this.workbench.activeTab] ?? renderers.dashboard)();
        const scope = document.createElement('p');
        scope.className = 'research-workbench-scope';
        scope.textContent = 'Scientific scope: this workbench manages imported computational data and artifacts; it does not diagnose Parkinson disease or create simulation evidence.';
        this.container.append(scope);
    }

    updateLive() {
        if (!this.container || this.workbench.activeTab !== 'dashboard') return;
        const dashboard = this.workbench.dashboard();
        const readout = this.container.querySelector('.research-live-readout');
        if (readout) readout.textContent = `Frame ${dashboard.currentFrame} / ${Math.max(0, dashboard.totalFrames - 1)} | ${dashboard.playbackStatus} | ${dashboard.currentBehavior ?? 'No behavior label'}`;
    }

    renderDashboard(content) {
        const dashboard = this.workbench.dashboard();
        content.append(this.heading('Scientific dashboard', `Frame ${dashboard.currentFrame} / ${Math.max(0, dashboard.totalFrames - 1)}`));
        const live = this.note('');
        live.classList.add('research-live-readout');
        live.textContent = `Frame ${dashboard.currentFrame} / ${Math.max(0, dashboard.totalFrames - 1)} | ${dashboard.playbackStatus} | ${dashboard.currentBehavior ?? 'No behavior label'}`;
        content.append(live);
        const grid = document.createElement('div');
        grid.className = 'research-metric-grid';
        Object.entries({
            Datasets: dashboard.datasets,
            Experiments: dashboard.experiments,
            Rollouts: dashboard.rollouts,
            'Selected fly': dashboard.selectedFly ?? 'n/a',
            Playback: dashboard.playbackStatus,
            Behavior: dashboard.currentBehavior ?? 'n/a',
            Validation: dashboard.validationStatus,
            'Computational index': dashboard.computationalIndex ?? 'n/a',
        }).forEach(([label, value]) => grid.append(this.metric(label, value)));
        content.append(grid);
        const stats = dashboard.currentStatistics;
        if (stats) content.append(this.note(`Current rollout statistics available: ${Object.keys(stats).length} summary fields.`));
        if (dashboard.analytics) content.append(this.note(`${dashboard.analytics.count ?? 0} filtered rollout summaries are available in Analytics.`));
    }

    renderComparison(content) {
        const comparison = this.workbench.experimentWorkspace?.comparison;
        if (!comparison) {
            content.append(this.heading('Comparison workspace', 'Unavailable'));
            return;
        }
        content.append(this.heading('Synchronized comparison', `${comparison.selectedExperimentIds.length} selected experiment(s)`));
        content.append(this.note('The existing comparison viewer consumes imported rollouts. These controls only configure synchronization state.'));
        const fields = [
            ['synchronized', 'Synchronized comparison'],
            ['syncCamera', 'Camera'],
            ['syncSelection', 'Selection'],
            ['syncTimeline', 'Timeline'],
            ['syncOverlays', 'Overlays'],
        ];
        const controls = document.createElement('div');
        controls.className = 'research-check-grid';
        fields.forEach(([key, label]) => {
            const wrapper = document.createElement('label');
            wrapper.className = 'research-check';
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.checked = Boolean(comparison[key]);
            input.addEventListener('change', () => {
                if (key === 'synchronized') comparison.setSynchronized(input.checked);
                else comparison.setSynchronization({ [key]: input.checked });
                this.changed();
            });
            wrapper.append(input, document.createTextNode(label));
            controls.append(wrapper);
        });
        content.append(controls);
        content.append(this.note(`Alignment: ${comparison.alignment.mode} | Frame: ${comparison.currentFrame}`));
    }

    renderValidation(content) {
        const report = this.workbench.validation.summarize();
        content.append(this.heading('Validation center', report.status));
        content.append(this.note(report.scope));
        if (!report.available) {
            content.append(this.note('No validation report is attached. Existing verification reports remain the source of truth.'));
            return;
        }
        Object.entries({ RMSE: report.rmse, MAE: report.mae, 'R2': report.r2, Correlation: report.correlation, Bootstrap: report.bootstrap, 'Cross validation': report.crossValidation, 'Effect size': report.effectSize, Outliers: report.outliers, 'Missing values': report.missingValues })
            .forEach(([label, value]) => content.append(this.metric(label, value ?? 'n/a')));
        if (report.warnings.length) content.append(this.note(`Warnings: ${report.warnings.length}`));
    }

    renderFigures(content) {
        content.append(this.heading('Figure workspace', `${this.workbench.figures.figures.length} composed figure(s)`));
        const create = document.createElement('button');
        create.type = 'button';
        create.textContent = 'New figure';
        create.addEventListener('click', () => { this.workbench.figures.create({ title: 'Untitled computational figure' }); this.changed(); });
        content.append(create);
        this.workbench.figures.list().forEach((figure) => {
            const row = document.createElement('div');
            row.className = 'research-list-row';
            row.textContent = `${figure.title} | ${figure.subplots.length} subplot(s) | ${figure.format.toUpperCase()}`;
            content.append(row);
        });
    }

    renderNotebook(content) {
        content.append(this.heading('Research notebook', `${this.workbench.notebook.entries.length} entry(ies)`));
        const input = document.createElement('textarea');
        input.className = 'research-notebook-input';
        input.placeholder = 'Add an observation or research note...';
        content.append(input);
        const add = document.createElement('button');
        add.type = 'button';
        add.textContent = 'Add observation';
        add.addEventListener('click', () => {
            if (input.value.trim()) { this.workbench.notebook.addObservation(input.value.trim(), { linkedRollout: this.workbench.workspace?.rollout?.source?.name ?? null }); this.changed(); }
        });
        content.append(add);
        this.workbench.notebook.list().slice().reverse().forEach((entry) => {
            const row = document.createElement('article');
            row.className = 'research-notebook-entry';
            row.innerHTML = `<strong>${escapeHTML(entry.type)}</strong><small>${escapeHTML(entry.timestamp)}</small><p>${escapeHTML(entry.content)}</p>`;
            content.append(row);
        });
    }

    renderBundle(content) {
        content.append(this.heading('Project packaging', 'Research Bundle metadata and checksum'));
        const bundle = this.workbench.bundle();
        content.append(this.note(`Manifest sections: ${bundle.manifest.sections.length} | Artifact references: ${bundle.manifest.artifactCount} | Checksum: ${bundle.checksum}`));
        const download = document.createElement('button');
        download.type = 'button';
        download.textContent = 'Download Research Bundle JSON';
        download.addEventListener('click', () => this.workbench.bundles.download(this.workbench.bundle()));
        content.append(download);
    }

    renderLayout(content) {
        const layout = this.workbench.layout;
        content.append(this.heading('Workspace layouts', `${layout.currentName} layout`));
        const select = document.createElement('select');
        select.innerHTML = layout.names().map((name) => `<option${name === layout.currentName ? ' selected' : ''}>${escapeHTML(name)}</option>`).join('');
        select.addEventListener('change', () => { layout.load(select.value); this.changed(); });
        content.append(select);
        const save = document.createElement('button');
        save.type = 'button';
        save.textContent = 'Save current layout';
        save.addEventListener('click', () => { layout.save(layout.currentName); this.changed(); });
        content.append(save);
        const reset = document.createElement('button');
        reset.type = 'button';
        reset.textContent = 'Reset layout';
        reset.addEventListener('click', () => { layout.reset(); this.changed(); });
        content.append(reset);
        content.append(this.note(`${layout.current.panels.length} panels | dock: ${layout.current.dock} | split view: ${layout.current.splitView}`));
    }

    heading(title, subtitle) {
        const node = document.createElement('div');
        node.className = 'research-section-heading';
        node.innerHTML = `<h3>${escapeHTML(title)}</h3><small>${escapeHTML(subtitle)}</small>`;
        return node;
    }

    metric(label, value) {
        const node = document.createElement('div');
        node.className = 'research-metric';
        node.innerHTML = `<strong>${escapeHTML(label)}</strong><span>${escapeHTML(value)}</span>`;
        return node;
    }

    note(text) {
        const node = document.createElement('p');
        node.className = 'muted research-note';
        node.textContent = text;
        return node;
    }

    changed() {
        this.render();
        this.onChange?.();
    }
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
}
