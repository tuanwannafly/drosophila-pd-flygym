/** Unified view over the existing laboratory, experiment and analytics services. */
export class LaboratoryDashboard {
    constructor({ laboratory, experimentWorkspace, analyticsDashboard }) {
        this.laboratory = laboratory;
        this.experimentWorkspace = experimentWorkspace;
        this.analyticsDashboard = analyticsDashboard;
        this.container = null;
        this.activeTab = 'home';
        this.tabs = [
            ['home', 'Home'],
            ['datasets', 'Datasets'],
            ['experiments', 'Experiments'],
            ['flies', 'Digital Fly'],
            ['analysis', 'Analysis'],
            ['reports', 'Reports'],
            ['publication', 'Publication'],
            ['plugins', 'Plugins'],
        ];
    }

    init(container) {
        this.container = container;
        this.render();
    }

    render(container = this.container) {
        if (!container) return null;
        this.container = container;
        container.replaceChildren();
        container.classList.add('laboratory-dashboard');
        const heading = document.createElement('div');
        heading.className = 'panel-heading laboratory-dashboard-heading';
        heading.innerHTML = '<h2>Digital Parkinson Laboratory</h2><span class="panel-status">Computational workspace</span>';
        container.append(heading);

        const navigation = document.createElement('nav');
        navigation.className = 'laboratory-dashboard-tabs';
        this.tabs.forEach(([key, label]) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = label;
            button.className = key === this.activeTab ? 'is-active' : '';
            button.addEventListener('click', () => {
                this.activeTab = key;
                this.render();
            });
            navigation.append(button);
        });
        container.append(navigation);

        const content = document.createElement('section');
        content.className = 'laboratory-dashboard-content';
        container.append(content);
        this.renderTab(content);
        const status = document.createElement('div');
        status.className = 'laboratory-status-bar';
        status.textContent = 'Scientific scope: computational data and software outputs only; no biological interpretation.';
        container.append(status);
        return this;
    }

    renderTab(content) {
        const renderers = {
            home: () => this.renderHome(content),
            datasets: () => this.renderDatasets(content),
            experiments: () => this.renderExperiments(content),
            flies: () => this.renderFlies(content),
            analysis: () => this.analyticsDashboard.render(content),
            reports: () => this.renderReports(content),
            publication: () => this.renderPublication(content),
            plugins: () => this.renderPlugins(content),
        };
        (renderers[this.activeTab] ?? renderers.home)();
    }

    renderHome(content) {
        const dashboard = this.laboratory.dashboard();
        const report = this.analyticsDashboard.compute();
        content.append(this.heading('Overview', 'Import → Digital Fly → Analysis → Validation → Report → Export'));
        const grid = document.createElement('div');
        grid.className = 'laboratory-summary-grid';
        Object.entries({
            Projects: dashboard.projects,
            Experiments: dashboard.experiments,
            Rollouts: this.experimentWorkspace.datasets.list().length,
            'Digital Flies': dashboard.flies,
            Analyses: dashboard.analyses,
            Reports: dashboard.reports,
            Exports: dashboard.exports,
            Plugins: dashboard.plugins,
        }).forEach(([label, value]) => grid.append(this.metric(label, value)));
        content.append(grid);
        const metrics = document.createElement('div');
        metrics.className = 'laboratory-metric-strip';
        Object.values(report.summary).forEach((item) => metrics.append(this.metric(item.label, formatNumber(item.mean))));
        content.append(this.heading('Scientific dashboard', 'Motion and behavioral summaries from loaded rollouts'));
        content.append(metrics);
        content.append(this.note('Use Analysis for charts and statistics. Validation and publication reports require caller-supplied reference data and are never synthesized by the browser.'));
    }

    renderDatasets(content) {
        const entries = this.experimentWorkspace.datasets.list();
        const validation = this.experimentWorkspace.datasets.validate(entries);
        content.append(this.heading('Dataset manager', `${validation.count} imported rollout${validation.count === 1 ? '' : 's'}`));
        content.append(this.note(`Valid: ${validation.valid} | Missing: ${validation.missing.length} | Duplicates: ${validation.duplicates.length} | Compatible: ${validation.compatible}`));
        entries.slice(0, 100).forEach((entry) => content.append(this.row(entry.id, `${entry.rollout?.source?.name ?? 'unnamed rollout'} | ${entry.rollout?.frameCount ?? 0} frames`)));
    }

    renderExperiments(content) {
        const records = this.experimentWorkspace.experiments.list();
        content.append(this.heading('Experiment browser', `${records.length} experiment${records.length === 1 ? '' : 's'}`));
        records.slice(0, 100).forEach((record) => content.append(this.row(record.name, `${record.kind} | ${record.rollouts.length} rollout${record.rollouts.length === 1 ? '' : 's'}`)));
    }

    renderFlies(content) {
        const flies = this.laboratory.listFlies();
        content.append(this.heading('Digital Fly browser', `${flies.length} imported Digital Fly instance${flies.length === 1 ? '' : 's'}`));
        flies.forEach((fly) => content.append(this.row(fly.name ?? fly.id, fly.trajectory ? 'trajectory attached' : 'no trajectory attached')));
        if (!flies.length) content.append(this.note('No Digital Fly is loaded.'));
    }

    renderReports(content) {
        const reports = this.laboratory.reports.list();
        content.append(this.heading('Report center', `${reports.length} report${reports.length === 1 ? '' : 's'}`));
        reports.forEach((report) => content.append(this.row(report.format, report.createdAt ?? '')));
        if (!reports.length) content.append(this.note('Reports are created from imported experiment data.'));
    }

    renderPublication(content) {
        const dashboard = this.laboratory.dashboard();
        content.append(this.heading('Publication center', 'Figures, tables, supplementary material and citation metadata'));
        content.append(this.note(`${dashboard.reports} report(s) and ${dashboard.exports} export(s) are available. Publication bundles use existing artifacts only.`));
    }

    renderPlugins(content) {
        const plugins = this.laboratory.pluginPlatform?.list?.() ?? [];
        content.append(this.heading('Plugin manager', `${plugins.length} registered plugin${plugins.length === 1 ? '' : 's'}`));
        plugins.forEach((plugin) => content.append(this.row(plugin.name ?? plugin.id, plugin.enabled === false ? 'disabled' : 'enabled')));
        if (!plugins.length) content.append(this.note('No plugins registered.'));
    }

    heading(title, subtitle) {
        const wrapper = document.createElement('div');
        wrapper.className = 'laboratory-section-heading';
        const heading = document.createElement('h3');
        heading.textContent = title;
        const detail = document.createElement('small');
        detail.textContent = subtitle;
        wrapper.append(heading, detail);
        return wrapper;
    }

    metric(label, value) {
        const card = document.createElement('div');
        card.className = 'laboratory-metric';
        card.innerHTML = `<strong>${escapeHTML(label)}</strong><span>${escapeHTML(value)}</span>`;
        return card;
    }

    row(title, detail) {
        const row = document.createElement('div');
        row.className = 'laboratory-list-row';
        row.innerHTML = `<strong>${escapeHTML(title)}</strong><small>${escapeHTML(detail)}</small>`;
        return row;
    }

    note(text) {
        const node = document.createElement('p');
        node.className = 'muted laboratory-note';
        node.textContent = text;
        return node;
    }
}

function formatNumber(value) {
    return Number.isFinite(value) ? value.toFixed(4) : 'n/a';
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
}
