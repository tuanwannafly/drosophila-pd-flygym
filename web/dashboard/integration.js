import { AnalysisBridge } from './analysis_bridge.js';
import { AssistantBridge } from './assistant_bridge.js';
import { DASHBOARD_TABS, DashboardState } from './state.js';
import { EventBus } from './event_bus.js';
import { ReportBridge } from './report_bridge.js';
import { SelectionBridge } from './selection.js';
import { WorkspaceSync } from './sync.js';
import { ViewerBridge } from './viewer_bridge.js';

/**
 * Composes existing browser modules into the Digital Laboratory shell.
 * This class owns navigation and synchronization only; data remains in Workspace.
 */
export class DigitalLaboratoryIntegration {
    constructor({
        workspace,
        laboratory,
        experimentWorkspace,
        laboratoryDashboard,
        chartRenderer,
        behaviorTimeline,
        threeViewer,
        viewportRenderer,
        reportGenerator,
        onLoadDataset = null,
    }) {
        this.workspace = workspace;
        this.laboratory = laboratory;
        this.experimentWorkspace = experimentWorkspace;
        this.laboratoryDashboard = laboratoryDashboard;
        this.onLoadDataset = onLoadDataset;
        this.eventBus = new EventBus();
        this.state = new DashboardState(workspace);
        this.selection = new SelectionBridge(workspace, this.eventBus);
        this.sync = new WorkspaceSync(workspace, this.eventBus);
        this.viewer = new ViewerBridge({ workspace, threeViewer, viewportRenderer });
        this.analysis = new AnalysisBridge({ workspace, chartRenderer, behaviorTimeline });
        this.reports = new ReportBridge({ laboratory, reportGenerator });
        this.assistant = new AssistantBridge({ workspace, experimentWorkspace, laboratory });
        this.container = null;
        this.unsubscribers = [];
        this.bindEvents();
    }

    init(container) {
        this.container = container;
        this.sync.start();
        this.analysis.attach(document.getElementById('rollout-charts'));
        this.render();
    }

    destroy() {
        this.sync.stop();
        this.unsubscribers.splice(0).forEach((unsubscribe) => unsubscribe());
        this.eventBus.clear();
    }

    bindEvents() {
        this.unsubscribers.push(
            this.eventBus.on('workspace:frame-changed', (event) => {
                this.state.notify();
                this.viewer.setFrame(event.frame);
                this.analysis.syncFrame(event.frame);
                this.updateLiveStatus();
            }),
            this.eventBus.on('workspace:playback-started', () => this.updateLiveStatus()),
            this.eventBus.on('workspace:playback-paused', () => this.updateLiveStatus()),
            this.eventBus.on('workspace:playback-stopped', () => this.updateLiveStatus()),
            this.eventBus.on('workspace:playback-finished', () => this.updateLiveStatus()),
            this.eventBus.on('selection:node', () => this.updateLiveStatus()),
            this.eventBus.on('selection:keyframe', () => this.updateLiveStatus()),
        );
    }

    setTab(tab) {
        this.state.setTab(tab);
        this.render();
        this.container?.scrollIntoView?.({ block: 'nearest' });
    }

    render() {
        if (!this.container) return;
        this.container.replaceChildren();
        this.container.className = 'digital-laboratory-dashboard';

        const heading = document.createElement('div');
        heading.className = 'panel-heading digital-laboratory-heading';
        heading.innerHTML = '<h2>Digital Laboratory</h2><span class="panel-status">Integrated computational workspace</span>';
        this.container.append(heading);

        const navigation = document.createElement('nav');
        navigation.className = 'digital-laboratory-tabs';
        navigation.setAttribute('aria-label', 'Digital Laboratory sections');
        DASHBOARD_TABS.forEach(([key, label]) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = label;
            button.className = key === this.state.activeTab ? 'is-active' : '';
            button.setAttribute('aria-current', key === this.state.activeTab ? 'page' : 'false');
            button.addEventListener('click', () => this.setTab(key));
            navigation.append(button);
        });
        this.container.append(navigation);

        const content = document.createElement('section');
        content.className = 'digital-laboratory-content';
        this.container.append(content);
        this.renderTab(content);

        const status = document.createElement('div');
        status.className = 'digital-laboratory-live-status';
        this.container.append(status);
        this.updateLiveStatus();
    }

    renderTab(content) {
        const renderers = {
            home: () => this.laboratoryDashboard?.renderHome?.(content),
            datasets: () => this.renderDatasets(content),
            viewer: () => this.renderViewer(content),
            analysis: () => this.renderAnalysis(content),
            validation: () => this.renderValidation(content),
            reports: () => this.reports.renderReports(content),
            publication: () => this.reports.renderPublication(content),
            plugins: () => this.laboratoryDashboard?.renderPlugins?.(content),
            assistant: () => this.assistant.render(content),
        };
        (renderers[this.state.activeTab] ?? renderers.home)();
        if (!content.children.length) content.append(this.note('No data is loaded in this section.'));
    }

    renderDatasets(content) {
        const load = document.createElement('button');
        load.type = 'button';
        load.textContent = 'Load dataset JSON';
        load.addEventListener('click', () => this.openDatasetPicker());
        content.append(load);
        this.laboratoryDashboard?.renderDatasets?.(content);
    }

    renderViewer(content) {
        const status = this.viewer.status();
        content.append(this.heading('Viewer', status.loaded ? 'viewer_pose.json or imported rollout loaded' : 'No dataset loaded'));
        content.append(this.note('Timeline, selection, Inspector, COM, skeleton and playback use the shared Workspace state.'));
        const controls = document.createElement('div');
        controls.className = 'digital-laboratory-actions';
        controls.append(this.action('Focus selected', () => this.viewer.focusSelection()));
        controls.append(this.action('Reset view', () => this.viewer.reset()));
        content.append(controls);
    }

    renderAnalysis(content) {
        if (this.workspace.rollout) {
            const charts = document.createElement('div');
            charts.className = 'digital-laboratory-analysis-charts';
            ['velocity', 'joint', 'com', 'angular', 'timeline', 'behavior'].forEach((type) => {
                const slot = document.createElement('div');
                slot.className = 'rollout-chart-slot';
                slot.dataset.chart = type;
                charts.append(slot);
            });
            content.append(charts);
            this.analysis.attach(charts);
            this.analysis.render();
            return;
        }
        content.append(this.note('Analysis charts require an imported FlyGym rollout.'));
    }

    renderValidation(content) {
        const report = this.experimentWorkspace?.validation?.summarize?.();
        content.append(this.heading('Validation', report?.status ?? 'No validation report'));
        content.append(this.note(report?.scope ?? 'Existing verification reports remain the source of truth; the browser does not synthesize validation.'));
    }

    openDatasetPicker() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json,application/json';
        input.addEventListener('change', () => {
            const file = input.files?.[0];
            if (file) this.onLoadDataset?.(file);
        });
        input.click();
    }

    updateLiveStatus() {
        if (!this.container) return;
        const status = this.container.querySelector('.digital-laboratory-live-status');
        if (!status) return;
        const snapshot = this.state.snapshot();
        status.textContent = `Frame ${snapshot.currentFrame} / ${Math.max(0, snapshot.totalFrames - 1)} | ${snapshot.playbackState} | ${snapshot.selectedNode ? 'Selection active' : 'No node selected'}`;
    }

    heading(title, subtitle) {
        const element = document.createElement('div');
        element.className = 'laboratory-section-heading';
        const titleElement = document.createElement('h3');
        titleElement.textContent = title;
        const subtitleElement = document.createElement('small');
        subtitleElement.textContent = subtitle;
        element.append(titleElement, subtitleElement);
        return element;
    }

    action(label, handler) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = label;
        button.addEventListener('click', handler);
        return button;
    }

    note(text) {
        const element = document.createElement('p');
        element.className = 'muted laboratory-note';
        element.textContent = text;
        return element;
    }
}
