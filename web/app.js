import { Timeline } from './timeline.js';
import { Sidebar } from './sidebar.js';
import { Toolbar } from './toolbar.js';
import { Workspace, WORKSPACE_EVENTS } from './workspace.js';
import { Layout } from './layout.js';
import { JSONLoader } from './json_loader.js';
import { Inspector } from './inspector.js';
import { ViewportRenderer } from './viewport_renderer.js';
import { PlaybackController } from './playback_controller.js';
import { FlyGymRolloutLoader } from './flygym_rollout.js';
import { computeRolloutStatistics } from './rollout_statistics.js';
import { BehaviorTimeline } from './behavior_timeline.js';
import { RolloutChartRenderer } from './rollout_charts.js';
import { RolloutExporter } from './rollout_export.js';
import { SessionRecorder } from './session_recorder.js';
import { WorkspacePersistence } from './workspace_persistence.js';
import { ExperimentWorkspace } from './experiment_workspace.js';
import { ExperimentWorkspacePanel } from './experiment_workspace_panel.js';
import { AnalyticsDashboard } from './experiment_analytics.js';
import { ExperimentReportGenerator } from './experiment_reports.js';
import { ExperimentComparisonModel } from './experiment_comparison.js';
import { DigitalLaboratory } from './digital_laboratory.js';
import { DigitalFly } from './digital_fly.js';
import { DigitalFly3D } from './digital_fly_3d.js';
import { LaboratoryDashboard } from './laboratory_dashboard.js';
import { RolloutComparisonViewer } from './comparison_viewer.js';
import { ResearchWorkbench } from './research_workbench.js';
import { ResearchWorkbenchPanel } from './research_workbench_panel.js';
import { Viewer } from './viewer/viewer.js';
import { DigitalLaboratoryIntegration } from './dashboard/integration.js';

export class App {
    constructor() {
        this.workspace = new Workspace();
        this.experimentWorkspace = new ExperimentWorkspace();
        this.laboratory = new DigitalLaboratory({ experimentWorkspace: this.experimentWorkspace });
        this.digitalFly = null;
        this.digitalFly3D = null;
        this.layout = new Layout();
        this.viewportRenderer = new ViewportRenderer(this.workspace, {
            onSelect: (node) => this.selectNode(node),
        });
        this.timeline = new Timeline(this.workspace, () => this.handleTimelineChange());
        this.sidebar = new Sidebar({ onSelectNode: (node) => this.selectNode(node) });
        this.inspector = new Inspector(this.workspace, () => this.handleInspectorChange());
        this.playbackController = new PlaybackController(this.workspace);
        this.threeViewer = new Viewer({
            onFrameChange: (frame) => this.playbackController.setFrame(frame),
        });
        this.behaviorTimeline = new BehaviorTimeline(this.workspace);
        this.chartRenderer = new RolloutChartRenderer();
        this.persistence = new WorkspacePersistence(this.workspace, globalThis.localStorage, this.experimentWorkspace);
        this.sessionRecorder = new SessionRecorder(this.workspace);
        this.analyticsDashboard = new AnalyticsDashboard(this.experimentWorkspace);
        this.laboratoryDashboard = new LaboratoryDashboard({
            laboratory: this.laboratory,
            experimentWorkspace: this.experimentWorkspace,
            analyticsDashboard: this.analyticsDashboard,
        });
        this.reportGenerator = new ExperimentReportGenerator(this.experimentWorkspace, this.analyticsDashboard);
        this.comparisonModel = new ExperimentComparisonModel(this.experimentWorkspace);
        this.comparisonViewer = new RolloutComparisonViewer();
        this.researchWorkbench = new ResearchWorkbench({
            workspace: this.workspace,
            experimentWorkspace: this.experimentWorkspace,
            laboratory: this.laboratory,
            analyticsDashboard: this.analyticsDashboard,
            viewportRenderer: this.viewportRenderer,
        });
        this.researchWorkbenchPanel = new ResearchWorkbenchPanel(this.researchWorkbench);
        this.experimentPanel = new ExperimentWorkspacePanel(this.experimentWorkspace, {
            onImport: (file, options) => this.loadSceneFile(file, options),
            onChange: () => this.renderExperimentWorkspace(),
            onReport: (format) => this.exportExperimentReport(format),
        });
        this.toolbar = new Toolbar({
            onLoadJSON: (file) => this.loadSceneFile(file),
            onResetView: () => this.activeViewer().resetView(),
            onUndo: () => this.undo(),
            onRedo: () => this.redo(),
            onInsert: () => this.insertKeyframe(),
            onDuplicate: () => this.duplicateKeyframes(),
            onDelete: () => this.deleteKeyframes(),
            onFramePrevious: () => this.nudgeSelectedKeyframe(-1),
            onFrameNext: () => this.nudgeSelectedKeyframe(1),
            onPlay: () => this.playbackController.play(),
            onPause: () => this.playbackController.pause(),
            onStop: () => this.playbackController.stop(),
            onLoop: (enabled) => this.playbackController.setLoop(enabled),
            onFps: (fps) => this.playbackController.setFps(fps),
            onSpeed: (speed) => this.playbackController.setSpeed(speed),
            onReverse: (enabled) => this.playbackController.setReverse(enabled),
            onTrajectoryVisibility: (visible) => this.setTrajectoryOption('visible', visible),
            onTrajectoryGhost: (enabled) => this.setTrajectoryOption('ghostTrail', enabled),
            onTrajectoryHistory: (enabled) => this.setTrajectoryOption('historyTrail', enabled),
            onTrajectoryColor: (color) => this.setTrajectoryOption('color', color),
            onTrajectoryThickness: (thickness) => this.setTrajectoryOption('thickness', Number(thickness)),
            onTrajectorySmoothing: (enabled) => this.setTrajectoryOption('smoothing', enabled),
            onSaveWorkspace: () => this.saveWorkspace(),
            onRestoreWorkspace: () => this.restoreWorkspace(),
            onExportJSON: () => this.exportRollout('json'),
            onExportCSV: () => this.exportRollout('csv'),
            onExportSVG: () => this.exportRollout('svg'),
            onRecordToggle: (recording) => this.toggleRecording(recording),
            onCameraType: (type) => this.activeViewer().setCameraType(type),
            onCameraPreset: (preset) => this.activeViewer().setCameraPreset(preset),
            onFocusSelected: () => this.activeViewer().focusBodyPart(),
            onOverlay: (name, enabled) => this.viewportRenderer.setOverlay(name, enabled),
            onBodyPartVisibility: (part, visible) => this.viewportRenderer.setBodyPartVisibility(part, visible),
            onMeshOpacity: (opacity) => this.viewportRenderer.setMeshOpacity(opacity),
            onExportPNG: () => this.viewportRenderer.exportPNG('fly-studio-view.png'),
            onExportViewSVG: () => this.viewportRenderer.exportSVG('fly-studio-view.svg'),
        });
        this.integration = new DigitalLaboratoryIntegration({
            workspace: this.workspace,
            laboratory: this.laboratory,
            experimentWorkspace: this.experimentWorkspace,
            laboratoryDashboard: this.laboratoryDashboard,
            chartRenderer: this.chartRenderer,
            behaviorTimeline: this.behaviorTimeline,
            threeViewer: this.threeViewer,
            viewportRenderer: this.viewportRenderer,
            reportGenerator: this.reportGenerator,
            onLoadDataset: (file) => this.loadSceneFile(file, { kind: 'Control' }),
        });
        this.keyDownHandler = (event) => this.handleKeyDown(event);
    }

    init() {
        console.log("Fly Studio Web Platform initializing...");
        this.workspace.load();
        const viewerRoot = document.getElementById('viewer');
        this.viewportRenderer.init(viewerRoot);
        this.threeViewer.init(viewerRoot);
        this.timeline.init(document.getElementById('timeline'));
        this.behaviorTimeline.init(document.getElementById('behavior-timeline'));
        this.experimentPanel.init(document.getElementById('experiment-manager'));
        this.researchWorkbenchPanel.init(document.getElementById('research-workbench'));
        this.integration.init(document.getElementById('experiment-dashboard'));
        this.sidebar.init(document.getElementById('sidebar'));
        this.inspector.init(document.getElementById('inspector'));
        this.toolbar.init(document.getElementById('toolbar'));
        this.toolbar.updatePlaybackState(this.workspace);
        this.bindWorkspaceEvents();
        this.persistence.startAutosave();
        window.addEventListener('keydown', this.keyDownHandler);

    }

    async loadSceneFile(file, experimentOptions = {}) {
        try {
            const rawData = await JSONLoader.parseRawFile(file);
            if (isViewerPoseDocument(rawData)) {
                await this.threeViewer.loadPose(rawData);
                this.workspace.load({
                    ...rawData,
                    animation: {
                        frames: rawData.frames,
                        duration: rawData.frame_count > 1 ? (rawData.frame_count - 1) / rawData.fps : 0,
                    },
                });
                this.workspace.fps = rawData.fps;
                this.digitalFly = null;
                this.digitalFly3D = null;
                this.viewportRenderer.setDigitalFly3D(null);
                this.viewportRenderer.canvas?.classList.add('hidden');
                document.getElementById('rollout-charts')?.replaceChildren();
                console.info('Loaded viewer pose', file.name);
                console.info('Frame count:', rawData.frame_count);
                console.info('Playback FPS:', rawData.fps);
            } else if (FlyGymRolloutLoader.canLoad(rawData)) {
                const rollout = FlyGymRolloutLoader.parseData(rawData, { sourceName: file.name });
                rollout.statistics = computeRolloutStatistics(rollout);
                this.workspace.loadRollout(rollout);
                this.workspace.rolloutStatistics = rollout.statistics;
                this.digitalFly = DigitalFly.fromRollout(rollout, { name: file.name });
                this.digitalFly3D = DigitalFly3D.fromDigitalFly(this.digitalFly, { metadata: { source: 'FlyGym rollout' } });
                this.viewportRenderer.setDigitalFly3D(this.digitalFly3D);
                this.threeViewer.setDigitalFly3D(this.digitalFly3D);
                this.viewportRenderer.canvas?.classList.add('hidden');
                this.laboratory.registerFly(this.digitalFly);
                this.experimentWorkspace.importRollout(rollout, {
                    name: file.name.replace(/\.json$/i, ''),
                    kind: experimentOptions.kind ?? 'Control',
                    metadata: { sourceName: file.name, format: rollout.source.format },
                });
                this.persistence.addRecentFile({ name: file.name, type: 'flygym-rollout' });
                this.renderRolloutViews();
                console.info('Loaded FlyGym rollout', file.name);
                console.info('Rollout format:', rollout.source.format);
                console.info('Frame count:', rollout.frameCount);
                console.info('Trajectory channels:', Object.keys(rollout.channels));
            } else {
                const data = JSONLoader.validateScene(rawData);
                const summary = JSONLoader.summarizeScene(data);

                // Commit the new state only after parsing and validation succeed.
                this.workspace.load(data);
                this.digitalFly = null;
                this.digitalFly3D = null;
                this.viewportRenderer.setDigitalFly3D(null);
                this.threeViewer.clear();
                this.viewportRenderer.canvas?.classList.remove('hidden');
                this.persistence.addRecentFile({ name: file.name, type: 'scene' });
                document.getElementById('rollout-charts')?.replaceChildren();
                console.info('Loaded scene', file.name);
                console.info('Node count:', summary.nodeCount);
                console.info('Camera count:', summary.cameraCount);
                console.info('Trajectory count:', summary.trajectoryCount);
            }
            this.timeline.render();
            this.sidebar.render(this.workspace.data, this.workspace.selectedNode);
            this.inspector.render();
            this.viewportRenderer.render();
            this.behaviorTimeline.render();
            this.renderExperimentWorkspace();
        } catch (error) {
            console.error('Failed to load scene JSON:', error);
            window.alert(`Unable to load scene JSON: ${error.message}`);
        }
    }

    selectNode(node) {
        const nodes = Array.isArray(this.workspace.data?.nodes) ? this.workspace.data.nodes : [];
        const canonicalNode = nodes.find((candidate) => (
            candidate === node
            || (node?.id && candidate?.id === node.id)
            || (node?.name && candidate?.name === node.name)
        )) ?? node;
        this.workspace.selectNode(canonicalNode);
        this.integration?.selection.syncFromWorkspace();
        this.sidebar.render(this.workspace.data, this.workspace.selectedNode);
        this.inspector.render();
        this.viewportRenderer.render();
        console.info('Selected node:', canonicalNode?.name ?? canonicalNode?.id ?? canonicalNode?.type ?? canonicalNode?.kind ?? 'Unnamed node');
    }

    handleTimelineChange() {
        this.inspector.render();
        if (this.threeViewer.digitalFly3D) this.threeViewer.setFrame(this.workspace.currentFrame);
        this.viewportRenderer.render();
    }

    handleInspectorChange() {
        this.timeline.render();
        this.inspector.render();
        if (this.threeViewer.digitalFly3D) this.threeViewer.setFrame(this.workspace.currentFrame);
        this.viewportRenderer.render();
    }

    insertKeyframe() {
        this.runEdit(() => this.workspace.insertKeyframe());
    }

    duplicateKeyframes() {
        this.runEdit(() => this.workspace.duplicateSelectedKeyframes());
    }

    deleteKeyframes() {
        this.runEdit(() => this.workspace.deleteSelectedKeyframes());
    }

    nudgeSelectedKeyframe(delta) {
        const frame = this.workspace.selectedKeyframe?.frame;
        if (!Number.isInteger(frame)) return;
        this.runEdit(() => this.workspace.moveSelectedKeyframe(frame + delta));
    }

    undo() {
        if (this.workspace.undo()) this.refreshEditor();
    }

    redo() {
        if (this.workspace.redo()) this.refreshEditor();
    }

    runEdit(operation) {
        const result = operation();
        if (result?.updated) this.refreshEditor();
        return result;
    }

    refreshEditor() {
        this.timeline.render();
        this.inspector.render();
        this.viewportRenderer.render();
    }

    handlePlaybackChange() {
        this.timeline.updatePlaybackDisplay();
        this.behaviorTimeline.updateFrame();
        this.viewportRenderer.render();
        if (this.threeViewer.digitalFly3D) this.threeViewer.setFrame(this.workspace.currentFrame);
        this.toolbar.updatePlaybackState(this.workspace);
        const comparison = this.experimentWorkspace.comparison;
        if (comparison.syncTimeline) {
            comparison.setFrame(this.workspace.currentFrame);
            this.comparisonViewer.setFrame(this.workspace.currentFrame);
        }
        this.researchWorkbenchPanel.updateLive();
    }

    activeViewer() {
        return this.threeViewer.digitalFly3D ? this.threeViewer : this.viewportRenderer;
    }

    setTrajectoryOption(name, value) {
        this.workspace.trajectorySettings[name] = value;
        this.viewportRenderer.render();
        this.toolbar.updatePlaybackState(this.workspace);
    }

    renderRolloutViews() {
        const chartRoot = document.getElementById('rollout-charts');
        if (!chartRoot || !this.workspace.rollout) return;
        chartRoot.innerHTML = `
            ${['velocity', 'joint', 'com', 'angular', 'timeline', 'behavior'].map((type) => `
                <div class="rollout-chart-slot" data-chart="${type}"></div>
            `).join('')}
        `;
        const targets = Object.fromEntries([...chartRoot.querySelectorAll('[data-chart]')]
            .map((element) => [element.dataset.chart, element]));
        this.chartRenderer.renderAll(targets, this.workspace.rollout);
    }

    renderExperimentWorkspace() {
        this.experimentPanel.render();
        const dashboardRoot = document.getElementById('experiment-dashboard');
        if (this.integration) this.integration.render();
        else this.laboratoryDashboard.render(dashboardRoot);
        const comparisonRoot = document.getElementById('comparison-viewer');
        if (comparisonRoot) this.comparisonViewer.render(comparisonRoot, this.comparisonModel.report());
        this.researchWorkbenchPanel.render();
    }

    exportExperimentReport(format) {
        if (format === 'pdf') {
            this.reportGenerator.printPDF();
            return;
        }
        this.reportGenerator.download(format);
    }

    saveWorkspace() {
        this.experimentWorkspace.saveSnapshot('manual-save', {
            camera: {
                ...this.viewportRenderer.getViewState(),
            },
            timeline: { currentFrame: this.workspace.currentFrame, totalFrames: this.workspace.totalFrames },
            selection: { node: this.workspace.selectedNode, keyframe: this.workspace.selectedKeyframe },
            workspace: { currentFrame: this.workspace.currentFrame, currentTime: this.workspace.currentTime },
            statistics: this.workspace.rolloutStatistics,
        });
        this.persistence.save('manual-save');
        console.info('Workspace saved.');
    }

    restoreWorkspace() {
        try {
            const snapshot = this.persistence.restore('manual-save');
            if (snapshot) {
                const experimentSnapshot = this.experimentWorkspace.snapshots.list()[0]?.state;
                if (experimentSnapshot?.camera) {
                    this.viewportRenderer.camera.restore(experimentSnapshot.camera);
                    this.viewportRenderer.syncLegacyCamera();
                }
                if (this.workspace.rollout) this.renderRolloutViews();
                this.refreshEditor();
                this.behaviorTimeline.render();
                this.renderExperimentWorkspace();
            }
        } catch (error) {
            console.error('Failed to restore workspace:', error);
            window.alert(`Unable to restore workspace: ${error.message}`);
        }
    }

    exportRollout(format) {
        const rollout = this.workspace.rollout;
        if (!rollout) {
            window.alert('Load a FlyGym rollout before exporting rollout data.');
            return;
        }
        const base = rollout.source.name?.replace(/\.json$/i, '') ?? 'flygym-rollout';
        if (format === 'json') RolloutExporter.download(RolloutExporter.toJSON(rollout, { pretty: true }), `${base}.json`, 'application/json');
        if (format === 'csv') RolloutExporter.download(RolloutExporter.toCSV(rollout), `${base}-thorax.csv`, 'text/csv');
        if (format === 'svg') RolloutExporter.exportSVG('velocity', rollout, `${base}-velocity.svg`);
    }

    toggleRecording(recording) {
        if (recording) {
            this.sessionRecorder.start({ source: this.workspace.rollout?.source ?? null });
            return;
        }
        const recordingData = this.sessionRecorder.stop();
        if (recordingData.length) {
            const recording = this.sessionRecorder.export();
            this.persistence.addRecentSession({
                savedAt: recording.events[0]?.time ?? new Date().toISOString(),
                eventCount: recording.events.length,
            });
            console.info('Session recording:', recording);
            RolloutExporter.download(
                JSON.stringify(recording, null, 2),
                'fly-studio-session-recording.json',
                'application/json',
            );
        }
    }

    bindWorkspaceEvents() {
        Object.values(WORKSPACE_EVENTS).forEach((eventName) => {
            this.workspace.on(eventName, () => this.handlePlaybackChange());
        });
    }

    handleKeyDown(event) {
        if (event.isComposing) return;
        const target = event.target;
        const editingText = target && (
            target.tagName === 'INPUT' || target.tagName === 'TEXTAREA'
        );
        if (editingText) return;

        const modifier = event.ctrlKey || event.metaKey;
        if (modifier && event.shiftKey && event.key.toLowerCase() === 'z') {
            event.preventDefault();
            this.redo();
        } else if (modifier && event.key.toLowerCase() === 'z') {
            event.preventDefault();
            this.undo();
        } else if (modifier && event.key.toLowerCase() === 'd') {
            event.preventDefault();
            this.duplicateKeyframes();
        } else if (modifier && event.key.toLowerCase() === 'c') {
            event.preventDefault();
            this.workspace.copySelectedKeyframes();
        } else if (modifier && event.key.toLowerCase() === 'v') {
            event.preventDefault();
            this.runEdit(() => this.workspace.pasteKeyframes());
        } else if (!modifier && event.key === 'Delete') {
            event.preventDefault();
            this.deleteKeyframes();
        } else if (!modifier && event.key === 'Escape') {
            this.workspace.clearKeyframeSelection();
            this.refreshEditor();
        } else if (!modifier && event.key.toLowerCase() === 'a' && !editingText) {
            event.preventDefault();
            this.workspace.selectAllKeyframes();
            this.refreshEditor();
        } else if (!modifier && event.key.toLowerCase() === 'f' && !editingText) {
            event.preventDefault();
            this.viewportRenderer.focusAnimation();
        }
    }

}

function isViewerPoseDocument(data) {
    return Boolean(
        data
        && typeof data === 'object'
        && data.metadata
        && Number.isFinite(data.fps)
        && Number.isInteger(data.frame_count)
        && Array.isArray(data.frames),
    );
}
