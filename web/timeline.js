export class Timeline {
    constructor(workspace, onSeekFrame = null) {
        this.workspace = workspace;
        this.container = null;
        this.onSeekFrame = onSeekFrame;
        this.dragState = null;
        this.timelineZoom = 1;
        this.timelinePan = 0;
        this.hoverFrame = null;
        this.panState = null;
    }

    init(container) {
        this.container = container;
        this.render();
    }

    render() {
        if (!this.container) return;
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        const currentFrame = clamp(
            this.workspace.currentFrame,
            0,
            totalFrames - 1,
        );
        this.ensureFrameVisible(currentFrame, totalFrames);
        const range = this.getVisibleRange(totalFrames);
        const keyframes = this.workspace.getKeyframeEntries();
        this.container.innerHTML = `
            <div class="timeline-panel">
                <div class="timeline-readout">
                    <span class="timeline-current-frame">Current Frame: <strong>${currentFrame}</strong></span>
                    <span class="timeline-current-time">Current Time: <strong>${formatTime(this.workspace.currentTime)}</strong></span>
                    <span>Total Frames: <strong>${totalFrames}</strong></span>
                    <span class="timeline-playback-state">Playback: <strong>${this.workspace.playbackState}</strong></span>
                    <span>Keyframes: <strong>${keyframes.length}</strong></span>
                    <span class="timeline-selected-keyframe">Selected Keyframe: <strong>${getSelectedKeyframeFrame(this.workspace)}</strong></span>
                </div>
                <div class="timeline-track">
                    <div class="timeline-ruler" aria-label="Frame ruler">
                        ${renderRuler(range)}
                    </div>
                    <input
                        class="timeline-slider"
                        type="range"
                        min="0"
                        max="${totalFrames - 1}"
                        step="1"
                        value="${currentFrame}"
                        aria-label="Current frame"
                        ${totalFrames === 1 ? 'disabled' : ''}
                    >
                    <div class="timeline-current-indicator" style="left: ${this.frameToPercent(currentFrame, range)}%"></div>
                    ${this.hoverFrame === null ? '' : `<div class="timeline-hover-indicator" style="left: ${this.frameToPercent(this.hoverFrame, range)}%"><span>${this.hoverFrame}</span></div>`}
                    <div class="timeline-keyframes" aria-label="Animation keyframes">
                        ${keyframes.filter((entry) => entry.frame >= range.start && entry.frame <= range.end).map((entry) => renderKeyframeMarker(
                            entry,
                            currentFrame,
                            this.workspace.selectedKeyframes,
                            range,
                        )).join('')}
                    </div>
                </div>
                <div class="timeline-minimap" aria-label="Timeline overview">
                    <span class="timeline-minimap-current" style="left: ${(currentFrame / Math.max(1, totalFrames - 1)) * 100}%"></span>
                </div>
                <div class="timeline-view-controls">
                    <button class="timeline-zoom-out" type="button" aria-label="Zoom timeline out">−</button>
                    <span>Zoom ${this.timelineZoom.toFixed(1)}x</span>
                    <button class="timeline-zoom-in" type="button" aria-label="Zoom timeline in">+</button>
                </div>
            </div>
        `;

        const panel = this.container.querySelector('.timeline-panel');
        const track = this.container.querySelector('.timeline-track');
        const slider = this.container.querySelector('.timeline-slider');
        slider.addEventListener('input', (event) => {
            this.seek(Number(event.target.value));
        });
        track.addEventListener('wheel', (event) => {
            event.preventDefault();
            this.zoomTimeline(event.deltaY < 0 ? 1.25 : 0.8, event.offsetX / Math.max(1, track.clientWidth));
        }, { passive: false });
        track.addEventListener('pointermove', (event) => {
            if (this.dragState || this.panState) return;
            const frame = this.frameFromPointer(event, track);
            if (frame === this.hoverFrame) return;
            this.hoverFrame = frame;
            const indicator = this.container.querySelector('.timeline-hover-indicator');
            if (!indicator) {
                this.render();
                return;
            }
            const range = this.getVisibleRange(Math.max(1, this.workspace.totalFrames));
            indicator.style.left = `${this.frameToPercent(frame, range)}%`;
            const label = indicator.querySelector('span');
            if (label) label.textContent = String(frame);
        });
        track.addEventListener('pointerleave', () => {
            if (this.hoverFrame === null) return;
            this.hoverFrame = null;
            this.render();
        });
        track.addEventListener('pointerdown', (event) => {
            if (event.button !== 1) return;
            event.preventDefault();
            this.panState = { pointerId: event.pointerId, startX: event.clientX, startPan: this.timelinePan, track };
            track.setPointerCapture(event.pointerId);
        });
        track.addEventListener('pointerup', (event) => this.endPan(event));
        track.addEventListener('pointercancel', (event) => this.endPan(event));
        track.addEventListener('pointermove', (event) => this.panTimeline(event));
        this.container.querySelector('.timeline-zoom-in').addEventListener('click', () => this.zoomTimeline(1.25, 0.5));
        this.container.querySelector('.timeline-zoom-out').addEventListener('click', () => this.zoomTimeline(0.8, 0.5));
        this.container.querySelectorAll('.timeline-keyframe').forEach((marker) => {
            marker.addEventListener('click', (event) => {
                event.stopPropagation();
                const entry = keyframes.find((candidate) => (
                    candidate.frame === Number(marker.dataset.frame)
                ));
                if (entry) this.selectKeyframe(entry, event.shiftKey);
            });
            marker.addEventListener('contextmenu', (event) => {
                event.preventDefault();
                this.selectKeyframe(entry);
                const name = window.prompt('Keyframe name', entry.data?.name ?? `Frame ${entry.frame}`);
                if (name !== null && this.workspace.renameSelectedKeyframe(name)) {
                    this.refreshAfterEdit();
                }
            });
            marker.addEventListener('keydown', (event) => {
                if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
                    event.preventDefault();
                    const delta = event.key === 'ArrowLeft' ? -1 : 1;
                    const result = this.workspace.moveSelectedKeyframe(entry.frame + delta);
                    if (result?.updated) this.refreshAfterEdit();
                } else if (event.key === 'Delete') {
                    event.preventDefault();
                    this.workspace.deleteSelectedKeyframes();
                    this.refreshAfterEdit();
                }
            });
            const entry = keyframes.find((candidate) => (
                candidate.frame === Number(marker.dataset.frame)
            ));
            if (!entry) return;
            marker.addEventListener('pointerdown', (event) => (
                this.startDrag(event, entry, marker, track)
            ));
            marker.addEventListener('pointermove', (event) => this.drag(event));
            marker.addEventListener('pointerup', (event) => this.endDrag(event));
            marker.addEventListener('pointercancel', (event) => this.endDrag(event));
        });
        slider.addEventListener('click', (event) => event.stopPropagation());
        panel.addEventListener('click', () => this.clearKeyframeSelection());
    }

    seek(frame) {
        this.workspace.setFrame(frame);
        this.render();
        if (this.onSeekFrame) this.onSeekFrame(this.workspace.currentFrame);
    }

    startDrag(event, entry, marker, track) {
        if (event.button !== 0) return;
        event.preventDefault();
        event.stopPropagation();
        this.workspace.selectKeyframe(entry.data, entry.frame, entry.sourceIndex);
        this.dragState = {
            entry,
            marker,
            pointerId: event.pointerId,
            track,
            totalFrames: Math.max(1, this.workspace.totalFrames),
            startFrame: entry.frame,
        };
        marker.setPointerCapture(event.pointerId);
        this.updateMarkerState();
        if (this.onSeekFrame) this.onSeekFrame(this.workspace.currentFrame);
    }

    drag(event) {
        if (!this.dragState || event.pointerId !== this.dragState.pointerId) return;
        event.preventDefault();
        const nextFrame = this.frameFromPointer(event, this.dragState.track);
        const result = this.workspace.moveSelectedKeyframe(nextFrame, { recordHistory: false });
        if (!result?.updated) {
            this.dragState.marker.classList.add('collision');
            return;
        }

        this.dragState.marker.classList.remove('collision');
        this.dragState.entry.frame = result.keyframe.frame;
        this.updateMarkerPosition(result.keyframe.frame);
        this.updateMarkerState();
        if (this.onSeekFrame) this.onSeekFrame(this.workspace.currentFrame);
    }

    endDrag(event) {
        if (!this.dragState || event.pointerId !== this.dragState.pointerId) return;
        if (this.dragState.marker.hasPointerCapture(event.pointerId)) {
            this.dragState.marker.releasePointerCapture(event.pointerId);
        }
        this.dragState.marker.classList.remove('collision');
        const { entry, startFrame } = this.dragState;
        const endFrame = entry.frame;
        if (endFrame !== startFrame) {
            this.workspace.recordCommand({
                label: 'Move keyframe',
                undo: () => this.workspace.setKeyframeFrame(entry, startFrame),
                redo: () => this.workspace.setKeyframeFrame(entry, endFrame),
            });
        }
        this.dragState = null;
    }

    frameFromPointer(event, track) {
        const bounds = track.getBoundingClientRect();
        if (bounds.width <= 0) return this.workspace.currentFrame;
        const ratio = clamp((event.clientX - bounds.left) / bounds.width, 0, 1);
        const range = this.getVisibleRange(Math.max(1, this.workspace.totalFrames));
        return Math.round(range.start + ratio * (range.end - range.start));
    }

    getVisibleRange(totalFrames) {
        const maximum = Math.max(0, totalFrames - 1);
        const span = maximum / this.timelineZoom;
        const start = clamp(this.timelinePan, 0, Math.max(0, maximum - span));
        return { start, end: Math.min(maximum, start + span) };
    }

    frameToPercent(frame, range) {
        if (range.end <= range.start) return 0;
        return clamp((frame - range.start) / (range.end - range.start), 0, 1) * 100;
    }

    ensureFrameVisible(frame, totalFrames) {
        const range = this.getVisibleRange(totalFrames);
        if (frame >= range.start && frame <= range.end) return;
        const span = range.end - range.start;
        this.timelinePan = clamp(frame - span / 2, 0, Math.max(0, totalFrames - 1 - span));
    }

    zoomTimeline(factor, anchorRatio = 0.5) {
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        const before = this.getVisibleRange(totalFrames);
        const anchor = before.start + anchorRatio * (before.end - before.start);
        this.timelineZoom = clamp(this.timelineZoom * factor, 1, 20);
        const afterSpan = (totalFrames - 1) / this.timelineZoom;
        this.timelinePan = clamp(anchor - anchorRatio * afterSpan, 0, Math.max(0, totalFrames - 1 - afterSpan));
        this.render();
    }

    panTimeline(event) {
        if (!this.panState || event.pointerId !== this.panState.pointerId) return;
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        const range = this.getVisibleRange(totalFrames);
        const bounds = this.panState.track.getBoundingClientRect();
        const framesPerPixel = (range.end - range.start) / Math.max(1, bounds.width);
        this.timelinePan = this.panState.startPan - (event.clientX - this.panState.startX) * framesPerPixel;
        this.timelinePan = clamp(this.timelinePan, 0, Math.max(0, totalFrames - 1 - (range.end - range.start)));
    }

    endPan(event) {
        if (!this.panState || event.pointerId !== this.panState.pointerId) return;
        if (this.panState.track.hasPointerCapture(event.pointerId)) this.panState.track.releasePointerCapture(event.pointerId);
        this.panState = null;
        this.render();
    }

    updateMarkerPosition(frame) {
        if (!this.dragState) return;
        const totalFrames = this.dragState.totalFrames;
        const percentage = this.frameToPercent(frame, this.getVisibleRange(totalFrames));
        this.dragState.marker.style.left = `${percentage}%`;
        this.dragState.marker.dataset.frame = String(frame);
        this.dragState.marker.setAttribute('aria-label', `Keyframe at frame ${frame}`);
        this.dragState.marker.title = `Keyframe ${frame}`;
        const currentReadout = this.container.querySelector('.timeline-current-frame strong');
        const selectedReadout = this.container.querySelector('.timeline-selected-keyframe strong');
        if (currentReadout) currentReadout.textContent = String(frame);
        if (selectedReadout) selectedReadout.textContent = String(frame);
    }

    updateMarkerState() {
        const currentFrame = this.workspace.currentFrame;
        const selectedKeyframes = this.workspace.selectedKeyframes;
        this.container.querySelectorAll('.timeline-keyframe').forEach((marker) => {
            const frame = Number(marker.dataset.frame);
            marker.classList.toggle('current', frame === currentFrame);
            marker.classList.toggle('selected', selectedKeyframes.some((entry) => entry.frame === frame));
        });
    }

    updatePlaybackDisplay() {
        if (!this.container) return;
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        const currentFrame = this.workspace.currentFrame;
        const previousPan = this.timelinePan;
        this.ensureFrameVisible(currentFrame, totalFrames);
        if (previousPan !== this.timelinePan) {
            this.render();
            return;
        }
        const range = this.getVisibleRange(totalFrames);
        const currentText = this.container.querySelector('.timeline-current-frame strong');
        const timeText = this.container.querySelector('.timeline-current-time strong');
        const playbackText = this.container.querySelector('.timeline-playback-state strong');
        const slider = this.container.querySelector('.timeline-slider');
        const indicator = this.container.querySelector('.timeline-current-indicator');
        if (!currentText || !timeText || !playbackText || !slider || !indicator) {
            this.render();
            return;
        }
        currentText.textContent = String(currentFrame);
        timeText.textContent = formatTime(this.workspace.currentTime);
        playbackText.textContent = this.workspace.playbackState;
        slider.value = String(currentFrame);
        indicator.style.left = `${this.frameToPercent(currentFrame, range)}%`;
        this.updateMarkerState();
    }

    refreshAfterEdit() {
        this.render();
        if (this.onSeekFrame) this.onSeekFrame(this.workspace.currentFrame);
    }

    selectKeyframe(entry, additive = false) {
        if (additive) {
            this.workspace.toggleKeyframeSelection(entry);
        } else {
            this.workspace.selectKeyframe(entry.data, entry.frame, entry.sourceIndex);
        }
        this.render();
        if (this.onSeekFrame) this.onSeekFrame(this.workspace.currentFrame);
    }

    clearKeyframeSelection() {
        if (!this.workspace.selectedKeyframe) return;
        this.workspace.clearKeyframeSelection();
        this.render();
        if (this.onSeekFrame) this.onSeekFrame(this.workspace.currentFrame);
    }
}

function renderKeyframeMarker(entry, currentFrame, selectedKeyframes, range) {
    const percentage = range.end <= range.start
        ? 0
        : clamp((entry.frame - range.start) / (range.end - range.start), 0, 1) * 100;
    const selected = selectedKeyframes.some((candidate) => (
        candidate.data === entry.data && candidate.sourceIndex === entry.sourceIndex
    )) ? ' selected' : '';
    const current = entry.frame === currentFrame ? ' current' : '';
    return `
        <button
            class="timeline-keyframe${selected}${current}"
            type="button"
            style="left: ${percentage}%"
            data-frame="${entry.frame}"
            aria-label="Keyframe at frame ${entry.frame}"
            title="Keyframe ${entry.frame}"
            tabindex="0"
        ></button>
    `;
}

function renderRuler(range) {
    if (range.end <= range.start) {
        return '<span class="timeline-ruler-tick" style="left: 0%">0</span>';
    }
    const count = Math.min(11, Math.max(2, Math.round(range.end - range.start) + 1));
    return Array.from({ length: count }, (_, index) => {
        const frame = Math.round(range.start + (index / (count - 1)) * (range.end - range.start));
        const percentage = (index / (count - 1)) * 100;
        return `<span class="timeline-ruler-tick" style="left: ${percentage}%">${frame}</span>`;
    }).join('');
}

function getSelectedKeyframeFrame(workspace) {
    return workspace.selectedKeyframe
        ? workspace.selectedKeyframe.frame
        : 'None';
}

function formatTime(time) {
    return `${Number(time || 0).toFixed(3)}s`;
}

function clamp(value, minimum, maximum) {
    const numericValue = Number.isFinite(value) ? value : minimum;
    return Math.min(maximum, Math.max(minimum, Math.round(numericValue)));
}
