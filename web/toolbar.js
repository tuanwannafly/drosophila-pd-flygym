export class Toolbar {
    constructor({
        onLoadJSON = null,
        onResetView = null,
        onUndo = null,
        onRedo = null,
        onInsert = null,
        onDuplicate = null,
        onDelete = null,
        onFramePrevious = null,
        onFrameNext = null,
        onPlay = null,
        onPause = null,
        onStop = null,
        onLoop = null,
        onFps = null,
        onSpeed = null,
        onReverse = null,
        onTrajectoryVisibility = null,
        onTrajectoryGhost = null,
        onTrajectoryHistory = null,
        onTrajectoryColor = null,
        onTrajectoryThickness = null,
        onTrajectorySmoothing = null,
        onSaveWorkspace = null,
        onRestoreWorkspace = null,
        onExportJSON = null,
        onExportCSV = null,
        onExportSVG = null,
        onRecordToggle = null,
        onCameraType = null,
        onCameraPreset = null,
        onFocusSelected = null,
        onOverlay = null,
        onBodyPartVisibility = null,
        onMeshOpacity = null,
        onExportPNG = null,
        onExportViewSVG = null,
    } = {}) {
        this.container = null;
        this.onLoadJSON = onLoadJSON;
        this.onResetView = onResetView;
        this.onUndo = onUndo;
        this.onRedo = onRedo;
        this.onInsert = onInsert;
        this.onDuplicate = onDuplicate;
        this.onDelete = onDelete;
        this.onFramePrevious = onFramePrevious;
        this.onFrameNext = onFrameNext;
        this.onPlay = onPlay;
        this.onPause = onPause;
        this.onStop = onStop;
        this.onLoop = onLoop;
        this.onFps = onFps;
        this.onSpeed = onSpeed;
        this.onReverse = onReverse;
        this.onTrajectoryVisibility = onTrajectoryVisibility;
        this.onTrajectoryGhost = onTrajectoryGhost;
        this.onTrajectoryHistory = onTrajectoryHistory;
        this.onTrajectoryColor = onTrajectoryColor;
        this.onTrajectoryThickness = onTrajectoryThickness;
        this.onTrajectorySmoothing = onTrajectorySmoothing;
        this.onSaveWorkspace = onSaveWorkspace;
        this.onRestoreWorkspace = onRestoreWorkspace;
        this.onExportJSON = onExportJSON;
        this.onExportCSV = onExportCSV;
        this.onExportSVG = onExportSVG;
        this.onRecordToggle = onRecordToggle;
        this.onCameraType = onCameraType;
        this.onCameraPreset = onCameraPreset;
        this.onFocusSelected = onFocusSelected;
        this.onOverlay = onOverlay;
        this.onBodyPartVisibility = onBodyPartVisibility;
        this.onMeshOpacity = onMeshOpacity;
        this.onExportPNG = onExportPNG;
        this.onExportViewSVG = onExportViewSVG;
    }

    init(container) {
        this.container = container;
        this.render();
    }

    render() {
        if (!this.container) return;
        this.container.innerHTML = `
            <div style="font-weight: bold; color: var(--accent);">Fly Studio Web</div>
            <div style="margin-left: 20px;">
                <button id="load-json-button" type="button">Load JSON</button>
                <input id="load-json-input" type="file" accept=".json,application/json" hidden>
                <button id="reset-view-button" type="button">Reset View</button>
                <label>Camera <select id="camera-type-input"><option value="perspective">Perspective</option><option value="orthographic">Orthographic</option></select></label>
                <label>Preset <select id="camera-preset-input"><option>Front</option><option>Back</option><option>Left</option><option>Right</option><option>Top</option><option>Bottom</option><option selected>Isometric</option></select></label>
                <button id="focus-selected-button" type="button">Focus Selected</button>
                <label>Mesh <input id="mesh-overlay-input" type="checkbox" checked></label>
                <label>Skeleton <input id="skeleton-overlay-input" type="checkbox" checked></label>
                <label>Axes <input id="axes-overlay-input" type="checkbox" checked></label>
                <label>COM <input id="com-overlay-input" type="checkbox" checked></label>
                <label>Labels <input id="labels-overlay-input" type="checkbox"></label>
                <label>Velocity <input id="velocity-overlay-input" type="checkbox"></label>
                <label>Angular <input id="angular-overlay-input" type="checkbox"></label>
                <label>Acceleration <input id="acceleration-overlay-input" type="checkbox"></label>
                <label>Angular acceleration <input id="angular-acceleration-overlay-input" type="checkbox"></label>
                <label>Contacts <input id="contacts-overlay-input" type="checkbox" checked></label>
                <label>Heatmap <input id="heatmap-overlay-input" type="checkbox"></label>
                <label>Parts <select id="body-part-input"><option value="all">All parts</option><option value="head">Head</option><option value="thorax">Thorax</option><option value="abdomen">Abdomen</option><option value="legs">Legs</option><option value="wings">Wings</option><option value="eyes">Eyes</option><option value="antenna">Antenna</option></select></label>
                <label>Opacity <input id="mesh-opacity-input" type="range" min="0" max="1" step="0.05" value="0.78"></label>
                <button id="export-view-png-button" type="button">PNG</button>
                <button id="export-view-svg-button" type="button">SVG</button>
                <button id="undo-button" type="button">Undo</button>
                <button id="redo-button" type="button">Redo</button>
                <button id="insert-keyframe-button" type="button">Insert Keyframe</button>
                <button id="duplicate-keyframe-button" type="button">Duplicate</button>
                <button id="delete-keyframe-button" type="button">Delete</button>
                <button id="frame-previous-button" type="button">Frame -</button>
                <button id="frame-next-button" type="button">Frame +</button>
                <button id="play-button" type="button">Play</button>
                <button id="pause-button" type="button">Pause</button>
                <button id="stop-button" type="button">Stop</button>
                <label>Loop <input id="loop-input" type="checkbox"></label>
                <label>FPS <input id="fps-input" type="number" min="1" step="1" value="30"></label>
                <label>Speed <input id="speed-input" type="number" min="0.1" step="0.1" value="1"></label>
                <label>Reverse <input id="reverse-input" type="checkbox"></label>
                <label>Trail <input id="trajectory-visible-input" type="checkbox" checked></label>
                <label>Ghost <input id="trajectory-ghost-input" type="checkbox" checked></label>
                <label>History <input id="trajectory-history-input" type="checkbox" checked></label>
                <label>Trail Color <input id="trajectory-color-input" type="color" value="#58c4dd"></label>
                <label>Trail Width <input id="trajectory-thickness-input" type="number" min="1" step="1" value="2"></label>
                <label>Smooth <input id="trajectory-smoothing-input" type="checkbox"></label>
                <button id="save-workspace-button" type="button">Save Workspace</button>
                <button id="restore-workspace-button" type="button">Restore</button>
                <button id="export-rollout-json-button" type="button">Export JSON</button>
                <button id="export-rollout-csv-button" type="button">Export CSV</button>
                <button id="export-rollout-svg-button" type="button">Export SVG</button>
                <label>Record <input id="record-session-input" type="checkbox"></label>
                <button type="button">Settings</button>
            </div>
        `;

        const loadButton = this.container.querySelector('#load-json-button');
        const fileInput = this.container.querySelector('#load-json-input');
        const resetViewButton = this.container.querySelector('#reset-view-button');
        const cameraTypeInput = this.container.querySelector('#camera-type-input');
        const cameraPresetInput = this.container.querySelector('#camera-preset-input');
        const focusSelectedButton = this.container.querySelector('#focus-selected-button');
        const bodyPartInput = this.container.querySelector('#body-part-input');
        const meshOpacityInput = this.container.querySelector('#mesh-opacity-input');
        const exportViewPNGButton = this.container.querySelector('#export-view-png-button');
        const exportViewSVGButton = this.container.querySelector('#export-view-svg-button');
        const undoButton = this.container.querySelector('#undo-button');
        const redoButton = this.container.querySelector('#redo-button');
        const insertButton = this.container.querySelector('#insert-keyframe-button');
        const duplicateButton = this.container.querySelector('#duplicate-keyframe-button');
        const deleteButton = this.container.querySelector('#delete-keyframe-button');
        const framePreviousButton = this.container.querySelector('#frame-previous-button');
        const frameNextButton = this.container.querySelector('#frame-next-button');
        const playButton = this.container.querySelector('#play-button');
        const pauseButton = this.container.querySelector('#pause-button');
        const stopButton = this.container.querySelector('#stop-button');
        const loopInput = this.container.querySelector('#loop-input');
        const fpsInput = this.container.querySelector('#fps-input');
        const speedInput = this.container.querySelector('#speed-input');
        const reverseInput = this.container.querySelector('#reverse-input');
        const trajectoryVisibleInput = this.container.querySelector('#trajectory-visible-input');
        const trajectoryGhostInput = this.container.querySelector('#trajectory-ghost-input');
        const trajectoryHistoryInput = this.container.querySelector('#trajectory-history-input');
        const trajectoryColorInput = this.container.querySelector('#trajectory-color-input');
        const trajectoryThicknessInput = this.container.querySelector('#trajectory-thickness-input');
        const trajectorySmoothingInput = this.container.querySelector('#trajectory-smoothing-input');
        const saveWorkspaceButton = this.container.querySelector('#save-workspace-button');
        const restoreWorkspaceButton = this.container.querySelector('#restore-workspace-button');
        const exportJSONButton = this.container.querySelector('#export-rollout-json-button');
        const exportCSVButton = this.container.querySelector('#export-rollout-csv-button');
        const exportSVGButton = this.container.querySelector('#export-rollout-svg-button');
        const recordSessionInput = this.container.querySelector('#record-session-input');
        cameraTypeInput.addEventListener('change', () => { if (this.onCameraType) this.onCameraType(cameraTypeInput.value); });
        cameraPresetInput.addEventListener('change', () => { if (this.onCameraPreset) this.onCameraPreset(cameraPresetInput.value); });
        focusSelectedButton.addEventListener('click', () => { if (this.onFocusSelected) this.onFocusSelected(); });
        bodyPartInput.addEventListener('change', () => {
            if (!this.onBodyPartVisibility) return;
            const parts = ['head', 'thorax', 'abdomen', 'legs', 'wings', 'eyes', 'antenna'];
            parts.forEach((part) => this.onBodyPartVisibility(part, bodyPartInput.value === 'all' || bodyPartInput.value === part));
        });
        ['mesh', 'skeleton', 'axes', 'com', 'labels', 'velocity', 'angular', 'acceleration', 'angular-acceleration', 'contacts', 'heatmap'].forEach((name) => {
            const input = this.container.querySelector(`#${name}-overlay-input`);
            input.addEventListener('change', () => { if (this.onOverlay) this.onOverlay(name, input.checked); });
        });
        meshOpacityInput.addEventListener('input', () => { if (this.onMeshOpacity) this.onMeshOpacity(meshOpacityInput.value); });
        exportViewPNGButton.addEventListener('click', () => { if (this.onExportPNG) this.onExportPNG(); });
        exportViewSVGButton.addEventListener('click', () => { if (this.onExportViewSVG) this.onExportViewSVG(); });
        loadButton.addEventListener('click', () => fileInput.click());
        resetViewButton.addEventListener('click', () => {
            if (this.onResetView) this.onResetView();
        });
        undoButton.addEventListener('click', () => { if (this.onUndo) this.onUndo(); });
        redoButton.addEventListener('click', () => { if (this.onRedo) this.onRedo(); });
        insertButton.addEventListener('click', () => { if (this.onInsert) this.onInsert(); });
        duplicateButton.addEventListener('click', () => { if (this.onDuplicate) this.onDuplicate(); });
        deleteButton.addEventListener('click', () => { if (this.onDelete) this.onDelete(); });
        framePreviousButton.addEventListener('click', () => { if (this.onFramePrevious) this.onFramePrevious(); });
        frameNextButton.addEventListener('click', () => { if (this.onFrameNext) this.onFrameNext(); });
        playButton.addEventListener('click', () => { if (this.onPlay) this.onPlay(); });
        pauseButton.addEventListener('click', () => { if (this.onPause) this.onPause(); });
        stopButton.addEventListener('click', () => { if (this.onStop) this.onStop(); });
        loopInput.addEventListener('change', () => { if (this.onLoop) this.onLoop(loopInput.checked); });
        fpsInput.addEventListener('change', () => { if (this.onFps) this.onFps(fpsInput.value); });
        speedInput.addEventListener('change', () => { if (this.onSpeed) this.onSpeed(speedInput.value); });
        reverseInput.addEventListener('change', () => { if (this.onReverse) this.onReverse(reverseInput.checked); });
        trajectoryVisibleInput.addEventListener('change', () => { if (this.onTrajectoryVisibility) this.onTrajectoryVisibility(trajectoryVisibleInput.checked); });
        trajectoryGhostInput.addEventListener('change', () => { if (this.onTrajectoryGhost) this.onTrajectoryGhost(trajectoryGhostInput.checked); });
        trajectoryHistoryInput.addEventListener('change', () => { if (this.onTrajectoryHistory) this.onTrajectoryHistory(trajectoryHistoryInput.checked); });
        trajectoryColorInput.addEventListener('change', () => { if (this.onTrajectoryColor) this.onTrajectoryColor(trajectoryColorInput.value); });
        trajectoryThicknessInput.addEventListener('change', () => { if (this.onTrajectoryThickness) this.onTrajectoryThickness(trajectoryThicknessInput.value); });
        trajectorySmoothingInput.addEventListener('change', () => { if (this.onTrajectorySmoothing) this.onTrajectorySmoothing(trajectorySmoothingInput.checked); });
        saveWorkspaceButton.addEventListener('click', () => { if (this.onSaveWorkspace) this.onSaveWorkspace(); });
        restoreWorkspaceButton.addEventListener('click', () => { if (this.onRestoreWorkspace) this.onRestoreWorkspace(); });
        exportJSONButton.addEventListener('click', () => { if (this.onExportJSON) this.onExportJSON(); });
        exportCSVButton.addEventListener('click', () => { if (this.onExportCSV) this.onExportCSV(); });
        exportSVGButton.addEventListener('click', () => { if (this.onExportSVG) this.onExportSVG(); });
        recordSessionInput.addEventListener('change', () => { if (this.onRecordToggle) this.onRecordToggle(recordSessionInput.checked); });
        fileInput.addEventListener('change', async () => {
            const [file] = fileInput.files;
            if (file && this.onLoadJSON) await this.onLoadJSON(file);
            fileInput.value = '';
        });
    }

    updatePlaybackState(workspace) {
        if (!this.container) return;
        const state = workspace.playbackState;
        const playButton = this.container.querySelector('#play-button');
        const pauseButton = this.container.querySelector('#pause-button');
        const loopInput = this.container.querySelector('#loop-input');
        const fpsInput = this.container.querySelector('#fps-input');
        const speedInput = this.container.querySelector('#speed-input');
        const reverseInput = this.container.querySelector('#reverse-input');
        const trajectoryVisibleInput = this.container.querySelector('#trajectory-visible-input');
        const trajectoryGhostInput = this.container.querySelector('#trajectory-ghost-input');
        const trajectoryHistoryInput = this.container.querySelector('#trajectory-history-input');
        const trajectoryColorInput = this.container.querySelector('#trajectory-color-input');
        const trajectoryThicknessInput = this.container.querySelector('#trajectory-thickness-input');
        const trajectorySmoothingInput = this.container.querySelector('#trajectory-smoothing-input');
        if (playButton) playButton.disabled = state === 'Playing';
        if (pauseButton) pauseButton.disabled = state !== 'Playing';
        if (loopInput) loopInput.checked = Boolean(workspace.loop);
        if (fpsInput && document.activeElement !== fpsInput) fpsInput.value = workspace.fps;
        if (speedInput && document.activeElement !== speedInput) speedInput.value = workspace.speed;
        if (reverseInput) reverseInput.checked = Boolean(workspace.reverse);
        const settings = workspace.trajectorySettings ?? {};
        if (trajectoryVisibleInput) trajectoryVisibleInput.checked = settings.visible !== false;
        if (trajectoryGhostInput) trajectoryGhostInput.checked = settings.ghostTrail !== false;
        if (trajectoryHistoryInput) trajectoryHistoryInput.checked = settings.historyTrail !== false;
        if (trajectoryColorInput && settings.color) trajectoryColorInput.value = settings.color;
        if (trajectoryThicknessInput && settings.thickness) trajectoryThicknessInput.value = settings.thickness;
        if (trajectorySmoothingInput) trajectorySmoothingInput.checked = Boolean(settings.smoothing);
    }
}
