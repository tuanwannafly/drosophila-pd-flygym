/** UI controls for the Three.js viewer. Playback timing stays in viewer.js. */
export class TimelineController {
    constructor({
        onFrame = null,
        onPlay = null,
        onPause = null,
        onStop = null,
        onSpeed = null,
        onLoop = null,
        onReset = null,
        onCameraPreset = null,
        onAxes = null,
        onGrid = null,
        onFloor = null,
        onShadow = null,
    } = {}) {
        this.root = null;
        this.frameInput = null;
        this.frameReadout = null;
        this.timeReadout = null;
        this.fpsReadout = null;
        this.totalReadout = null;
        this.playButton = null;
        this.pauseButton = null;
        this.stopButton = null;
        this.speedInput = null;
        this.loopInput = null;
        this.cameraInput = null;
        this.callbacks = {
            onFrame,
            onPlay,
            onPause,
            onStop,
            onSpeed,
            onLoop,
            onReset,
            onCameraPreset,
            onAxes,
            onGrid,
            onFloor,
            onShadow,
        };
    }

    init(root) {
        this.root = root;
        root.replaceChildren();
        root.className = 'three-viewer-timeline';
        root.innerHTML = `
            <div class="three-viewer-controls" role="group" aria-label="Viewer playback controls">
                <button type="button" data-action="play">Play</button>
                <button type="button" data-action="pause">Pause</button>
                <button type="button" data-action="stop">Stop</button>
                <label>Speed <select data-role="speed"><option value="0.25">0.25x</option><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option><option value="4">4x</option></select></label>
                <label><input type="checkbox" data-role="loop"> Loop</label>
                <span data-role="frame-readout">Frame 0 / 0</span>
                <span data-role="time-readout">Time 0.000 s</span>
                <span data-role="fps-readout">FPS 0</span>
                <label>Camera <select data-role="camera"><option value="demo" selected>Demo</option><option value="isometric">Isometric</option><option value="front">Front</option><option value="left">Left</option><option value="top">Top</option></select></label>
                <button type="button" data-action="reset">Reset view</button>
                <label><input type="checkbox" data-role="axes" checked> Axes</label>
                <label><input type="checkbox" data-role="grid" checked> Grid</label>
                <label><input type="checkbox" data-role="floor" checked> Floor</label>
                <label><input type="checkbox" data-role="shadow" checked> Shadow</label>
            </div>
            <input data-role="frame" type="range" min="0" max="0" value="0" step="1" aria-label="Viewer frame">
        `;
        this.frameInput = root.querySelector('[data-role="frame"]');
        this.frameReadout = root.querySelector('[data-role="frame-readout"]');
        this.timeReadout = root.querySelector('[data-role="time-readout"]');
        this.fpsReadout = root.querySelector('[data-role="fps-readout"]');
        this.playButton = root.querySelector('[data-action="play"]');
        this.pauseButton = root.querySelector('[data-action="pause"]');
        this.stopButton = root.querySelector('[data-action="stop"]');
        this.speedInput = root.querySelector('[data-role="speed"]');
        this.loopInput = root.querySelector('[data-role="loop"]');
        this.cameraInput = root.querySelector('[data-role="camera"]');
        this.frameInput.addEventListener('input', () => this.callbacks.onFrame?.(Number(this.frameInput.value)));
        this.playButton.addEventListener('click', () => this.callbacks.onPlay?.());
        this.pauseButton.addEventListener('click', () => this.callbacks.onPause?.());
        this.stopButton.addEventListener('click', () => this.callbacks.onStop?.());
        root.querySelector('[data-action="reset"]').addEventListener('click', () => this.callbacks.onReset?.());
        this.speedInput.addEventListener('change', () => this.callbacks.onSpeed?.(Number(this.speedInput.value)));
        this.loopInput.addEventListener('change', () => this.callbacks.onLoop?.(this.loopInput.checked));
        this.cameraInput.addEventListener('change', () => this.callbacks.onCameraPreset?.(this.cameraInput.value));
        root.querySelector('[data-role="axes"]').addEventListener('change', (event) => this.callbacks.onAxes?.(event.target.checked));
        root.querySelector('[data-role="grid"]').addEventListener('change', (event) => this.callbacks.onGrid?.(event.target.checked));
        root.querySelector('[data-role="floor"]').addEventListener('change', (event) => this.callbacks.onFloor?.(event.target.checked));
        root.querySelector('[data-role="shadow"]').addEventListener('change', (event) => this.callbacks.onShadow?.(event.target.checked));
    }

    setRange(totalFrames) {
        const maximum = Math.max(0, Number(totalFrames) - 1);
        this.frameInput.max = String(maximum);
        this.setFrame(0, totalFrames);
    }

    setFrame(frame, totalFrames = Number(this.frameInput?.max ?? 0) + 1, details = {}) {
        if (!this.frameInput) return;
        const maximum = Math.max(0, Number(totalFrames) - 1);
        const current = Math.min(maximum, Math.max(0, Math.round(Number(frame) || 0)));
        this.frameInput.max = String(maximum);
        this.frameInput.value = String(current);
        this.frameReadout.textContent = `Frame ${current} / ${Math.max(0, Number(totalFrames) || 0)}`;
        if (this.timeReadout) this.timeReadout.textContent = `Time ${(Number(details.time) || 0).toFixed(3)} s`;
        if (this.fpsReadout) {
            const fps = Number(details.fps) || 0;
            const speed = Number(details.speed) || 1;
            this.fpsReadout.textContent = `FPS ${fps.toFixed(1)} | ${speed.toFixed(2)}x`;
        }
    }

    setPlaying(playing) {
        this.playButton?.toggleAttribute('disabled', Boolean(playing));
        this.pauseButton?.toggleAttribute('disabled', !playing);
    }

    destroy() {
        this.root?.replaceChildren();
        this.root = null;
    }
}
