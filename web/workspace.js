export const WORKSPACE_EVENTS = Object.freeze({
    FRAME_CHANGED: 'FrameChanged',
    PLAYBACK_STARTED: 'PlaybackStarted',
    PLAYBACK_PAUSED: 'PlaybackPaused',
    PLAYBACK_STOPPED: 'PlaybackStopped',
    PLAYBACK_LOOPED: 'PlaybackLooped',
    PLAYBACK_FINISHED: 'PlaybackFinished',
});

export class Workspace {
    constructor() {
        this.data = {};
        this.selectedNode = null;
        this.selectedKeyframe = null;
        this.selectedKeyframes = [];
        this.currentFrame = 0;
        this.currentTime = 0;
        this.totalFrames = 1;
        this.fps = 30;
        this.speed = 1;
        this.loop = false;
        this.reverse = false;
        this.trajectorySettings = {
            visible: true,
            ghostTrail: true,
            historyTrail: true,
            color: '#58c4dd',
            thickness: 2,
            smoothing: false,
        };
        this.animation = null;
        this.frames = [];
        this.duration = 0;
        this.rollout = null;
        this.rolloutStatistics = null;
        this.behaviorFilter = { query: '', labels: [], types: [] };
        this.playbackState = 'Stopped';
        this.clipboard = [];
        this.undoStack = [];
        this.redoStack = [];
        this.listeners = new Map();
    }

    on(eventName, listener) {
        if (typeof listener !== 'function') return () => {};
        const listeners = this.listeners.get(eventName) ?? new Set();
        listeners.add(listener);
        this.listeners.set(eventName, listeners);
        return () => this.off(eventName, listener);
    }

    off(eventName, listener) {
        this.listeners.get(eventName)?.delete(listener);
    }

    emit(eventName, detail = {}) {
        this.listeners.get(eventName)?.forEach((listener) => listener({
            type: eventName,
            workspace: this,
            ...detail,
        }));
    }

    load(data = null) {
        if (data !== null) {
            this.data = data;
            this.selectedNode = null;
            this.selectedKeyframe = null;
            this.selectedKeyframes = [];
            this.currentFrame = 0;
            this.currentTime = 0;
            this.playbackState = 'Stopped';
            this.clipboard = [];
            this.undoStack = [];
            this.redoStack = [];
            this.animation = getAnimation(data);
            this.frames = Array.isArray(this.animation?.frames)
                ? this.animation.frames
                : [];
            this.duration = getDuration(this.animation, data);
            this.totalFrames = this.frames.length > 0
                ? this.frames.length
                : getTotalFrames(data);
            this.rollout = data.flygymRollout ?? null;
            this.rolloutStatistics = null;
            this.behaviorFilter = { query: '', labels: [], types: [] };
            console.log('Workspace updated.');
            return this.data;
        }

        console.log('Workspace loaded.');
        return this.data;
    }

    loadRollout(rollout) {
        if (!rollout?.workspaceData) throw new Error('A normalized FlyGym rollout is required.');
        this.load(rollout.workspaceData);
        this.rollout = rollout;
        return this.rollout;
    }

    selectNode(node) {
        this.selectedNode = node || null;
        return this.selectedNode;
    }

    setFrame(frame, time = null) {
        const totalFrames = Math.max(1, this.totalFrames);
        const numericFrame = Number(frame);
        if (!Number.isFinite(numericFrame)) return this.currentFrame;
        const nextFrame = clamp(Math.round(numericFrame), 0, totalFrames - 1);
        const frameDuration = this.duration > 0 && totalFrames > 1
            ? this.duration / (totalFrames - 1)
            : 1 / Math.max(1, this.fps);
        const nextTime = time === null || time === undefined
            ? nextFrame * frameDuration
            : Math.max(0, Number(time) || 0);
        const changed = this.currentFrame !== nextFrame || this.currentTime !== nextTime;
        this.currentFrame = nextFrame;
        this.currentTime = nextTime;
        if (changed) {
            this.emit(WORKSPACE_EVENTS.FRAME_CHANGED, {
                frame: this.currentFrame,
                time: this.currentTime,
            });
        }
        return this.currentFrame;
    }

    selectKeyframe(keyframe, frame, sourceIndex = null) {
        const selectedFrame = Number(frame);
        if (!Number.isInteger(selectedFrame) || selectedFrame < 0) {
            this.selectedKeyframe = null;
            return this.selectedKeyframe;
        }

        this.selectedKeyframe = {
            frame: selectedFrame,
            data: keyframe,
            sourceIndex,
        };
        this.selectedKeyframes = [this.selectedKeyframe];
        this.setFrame(selectedFrame);
        return this.selectedKeyframe;
    }

    selectKeyframes(entries) {
        const selected = (Array.isArray(entries) ? entries : [])
            .filter((entry) => entry && Number.isInteger(entry.frame))
            .map((entry) => ({
                frame: entry.frame,
                data: entry.data,
                sourceIndex: entry.sourceIndex ?? null,
            }));
        this.selectedKeyframes = selected;
        this.selectedKeyframe = selected[0] ?? null;
        if (this.selectedKeyframe) this.setFrame(this.selectedKeyframe.frame);
        return this.selectedKeyframes;
    }

    toggleKeyframeSelection(entry) {
        const current = this.selectedKeyframes.filter((candidate) => (
            candidate.data !== entry?.data
            && candidate.sourceIndex !== entry?.sourceIndex
        ));
        if (current.length === this.selectedKeyframes.length) current.push(entry);
        return this.selectKeyframes(current);
    }

    selectAllKeyframes() {
        return this.selectKeyframes(this.getKeyframeEntries());
    }

    clearKeyframeSelection() {
        this.selectedKeyframe = null;
        this.selectedKeyframes = [];
        return this.selectedKeyframe;
    }

    getKeyframeSource() {
        if (Array.isArray(this.animation?.keyframes)) return this.animation.keyframes;
        if (Array.isArray(this.frames)) return this.frames;
        return null;
    }

    getKeyframeEntries() {
        const explicitKeyframes = Array.isArray(this.animation?.keyframes);
        const source = explicitKeyframes
            ? this.animation.keyframes
            : Array.isArray(this.frames) ? this.frames : [];
        const hasFlags = !explicitKeyframes && source.some((entry) => (
            entry
            && typeof entry === 'object'
            && (entry.keyframe !== undefined || entry.isKeyframe !== undefined)
        ));
        const totalFrames = Math.max(1, this.totalFrames);
        const entries = source
            .filter((entry) => !hasFlags || entry?.keyframe === true || entry?.isKeyframe === true)
            .map((entry, sourceIndex) => ({
                data: entry,
                frame: getKeyframeFrame(entry, sourceIndex),
                sourceIndex,
            }))
            .filter((entry) => Number.isInteger(entry.frame) && entry.frame >= 0)
            .map((entry) => ({
                ...entry,
                frame: Math.min(entry.frame, totalFrames - 1),
            }));
        const uniqueEntries = new Map();
        entries.forEach((entry) => {
            if (!uniqueEntries.has(entry.frame)) uniqueEntries.set(entry.frame, entry);
        });
        return [...uniqueEntries.values()].sort((left, right) => left.frame - right.frame);
    }

    moveSelectedKeyframe(frame, { recordHistory = true } = {}) {
        if (!this.selectedKeyframe) return null;

        const parsedFrame = Number(frame);
        if (!Number.isInteger(parsedFrame) || parsedFrame < 0) {
            return { updated: false, reason: 'invalid-frame', keyframe: this.selectedKeyframe };
        }

        const maximumFrame = Math.max(0, this.totalFrames - 1);
        const nextFrame = Math.min(parsedFrame, maximumFrame);
        const collision = this.getKeyframeEntries().some((entry) => (
            entry.frame === nextFrame
            && entry.data !== this.selectedKeyframe.data
            && entry.sourceIndex !== this.selectedKeyframe.sourceIndex
        ));
        if (collision) {
            return { updated: false, reason: 'collision', keyframe: this.selectedKeyframe };
        }

        const movedKeyframe = this.selectedKeyframe;
        const previousFrame = movedKeyframe.frame;
        const data = movedKeyframe.data;
        if (data && typeof data === 'object' && !Array.isArray(data)) {
            const positionKey = getPositionKey(data) || 'frame';
            data[positionKey] = nextFrame;
        }

        movedKeyframe.frame = nextFrame;
        this.syncSelectedKeyframeFrame(movedKeyframe);
        this.setFrame(nextFrame);
        if (recordHistory && previousFrame !== nextFrame) {
            this.recordCommand({
                label: 'Move keyframe',
                undo: () => this.setKeyframeFrame(movedKeyframe, previousFrame),
                redo: () => this.setKeyframeFrame(movedKeyframe, nextFrame),
            });
        }
        return { updated: true, keyframe: this.selectedKeyframe };
    }

    updateSelectedKeyframeFrame(frame) {
        const result = this.moveSelectedKeyframe(frame);
        return result?.keyframe ?? null;
    }

    updateSelectedKeyframeMetadata(metadata) {
        if (!this.selectedKeyframe) return null;
        const data = this.selectedKeyframe.data;
        if (!data || typeof data !== 'object' || Array.isArray(data)) {
            return this.selectedKeyframe;
        }

        const before = cloneValue(data.metadata);
        if (metadata === undefined) {
            delete data.metadata;
        } else {
            data.metadata = metadata;
        }
        this.recordCommand({
            label: 'Edit metadata',
            undo: () => setMetadata(data, before),
            redo: () => setMetadata(data, metadata),
        });
        return this.selectedKeyframe;
    }

    updateSelectedKeyframeDuration(duration) {
        if (!this.selectedKeyframe) return null;

        const parsedDuration = Number(duration);
        if (!Number.isFinite(parsedDuration) || parsedDuration < 0) {
            return this.selectedKeyframe;
        }

        const data = this.selectedKeyframe.data;
        const before = data && typeof data === 'object' && hasOwn(data, 'duration')
            ? data.duration
            : this.animation?.duration;
        if (data && typeof data === 'object' && !Array.isArray(data)
            && hasOwn(data, 'duration')) {
            data.duration = parsedDuration;
        } else if (this.animation && hasOwn(this.animation, 'duration')) {
            this.animation.duration = parsedDuration;
            this.duration = parsedDuration;
        }
        this.recordCommand({
            label: 'Edit duration',
            undo: () => setDuration(this, data, before),
            redo: () => setDuration(this, data, parsedDuration),
        });
        return this.selectedKeyframe;
    }

    renameSelectedKeyframe(name) {
        if (!this.selectedKeyframe || !this.selectedKeyframe.data
            || typeof this.selectedKeyframe.data !== 'object') return null;
        const nextName = String(name ?? '').trim();
        if (!nextName) return this.selectedKeyframe;
        const data = this.selectedKeyframe.data;
        const before = data.name;
        data.name = nextName;
        this.recordCommand({
            label: 'Rename keyframe',
            undo: () => { data.name = before; },
            redo: () => { data.name = nextName; },
        });
        return this.selectedKeyframe;
    }

    insertKeyframe(frame = this.currentFrame, data = {}) {
        const source = this.getKeyframeSource();
        const nextFrame = Number(frame);
        if (!source || !Number.isInteger(nextFrame) || nextFrame < 0) {
            return { updated: false, reason: 'invalid-frame' };
        }
        if (this.getKeyframeEntries().some((entry) => entry.frame === nextFrame)) {
            return { updated: false, reason: 'collision' };
        }

        const keyframe = cloneValue(data) || {};
        if (typeof keyframe !== 'object' || Array.isArray(keyframe)) return { updated: false, reason: 'invalid-data' };
        keyframe[getPositionKey(keyframe) || 'frame'] = nextFrame;
        source.push(keyframe);
        this.totalFrames = Math.max(this.totalFrames, nextFrame + 1);
        const entry = { data: keyframe, frame: nextFrame, sourceIndex: source.length - 1 };
        this.selectKeyframe(keyframe, nextFrame, entry.sourceIndex);
        this.recordCommand({
            label: 'Insert keyframe',
            undo: () => this.removeKeyframeData(keyframe),
            redo: () => this.restoreKeyframeData(keyframe),
        });
        return { updated: true, keyframe: entry };
    }

    deleteSelectedKeyframes() {
        const source = this.getKeyframeSource();
        const selected = [...this.selectedKeyframes];
        if (!source || selected.length === 0) return { updated: false, reason: 'no-selection' };
        const removed = selected
            .map((entry) => ({ data: entry.data, index: source.indexOf(entry.data) }))
            .filter((entry) => entry.index >= 0)
            .sort((left, right) => right.index - left.index);
        if (removed.length === 0) return { updated: false, reason: 'not-found' };
        removed.forEach((entry) => source.splice(entry.index, 1));
        this.clearKeyframeSelection();
        this.recordCommand({
            label: 'Delete keyframe',
            undo: () => removed.slice().reverse().forEach((entry) => source.splice(entry.index, 0, entry.data)),
            redo: () => removed.forEach((entry) => source.splice(source.indexOf(entry.data), 1)),
        });
        return { updated: true, count: removed.length };
    }

    duplicateSelectedKeyframes() {
        const selected = [...this.selectedKeyframes];
        if (selected.length === 0) return { updated: false, reason: 'no-selection' };
        const created = [];
        for (const entry of selected) {
            let frame = entry.frame + 1;
            while (this.getKeyframeEntries().some((candidate) => candidate.frame === frame)) frame += 1;
            const result = this.insertKeyframe(frame, entry.data);
            if (result.updated) created.push(result.keyframe);
        }
        if (created.length === 0) return { updated: false, reason: 'no-space' };
        this.selectKeyframes(created);
        return { updated: true, keyframes: created };
    }

    copySelectedKeyframes() {
        this.clipboard = this.selectedKeyframes.map((entry) => ({
            frame: entry.frame,
            data: cloneValue(entry.data),
        }));
        return this.clipboard;
    }

    pasteKeyframes(frame = this.currentFrame) {
        if (this.clipboard.length === 0) return { updated: false, reason: 'empty-clipboard' };
        const origin = this.clipboard[0].frame;
        const created = [];
        for (const item of this.clipboard) {
            const targetFrame = Number(frame) + item.frame - origin;
            const result = this.insertKeyframe(targetFrame, item.data);
            if (result.updated) created.push(result.keyframe);
        }
        if (created.length === 0) return { updated: false, reason: 'collision' };
        this.selectKeyframes(created);
        return { updated: true, keyframes: created };
    }

    recordCommand(command) {
        if (!command || typeof command.undo !== 'function' || typeof command.redo !== 'function') return;
        this.undoStack.push(command);
        this.redoStack = [];
    }

    undo() {
        const command = this.undoStack.pop();
        if (!command) return false;
        command.undo();
        this.redoStack.push(command);
        return true;
    }

    redo() {
        const command = this.redoStack.pop();
        if (!command) return false;
        command.redo();
        this.undoStack.push(command);
        return true;
    }

    setKeyframeFrame(entry, frame) {
        if (!entry) return;
        const data = entry.data;
        if (data && typeof data === 'object' && !Array.isArray(data)) {
            data[getPositionKey(data) || 'frame'] = frame;
        }
        entry.frame = frame;
        this.syncSelectedKeyframeFrame(entry);
        this.setFrame(frame);
    }

    syncSelectedKeyframeFrame(entry) {
        this.selectedKeyframes.forEach((candidate) => {
            if (candidate.data === entry.data) candidate.frame = entry.frame;
        });
        if (this.selectedKeyframe?.data === entry.data) this.selectedKeyframe.frame = entry.frame;
    }

    removeKeyframeData(data) {
        const source = this.getKeyframeSource();
        const index = source?.indexOf(data) ?? -1;
        if (index >= 0) source.splice(index, 1);
        this.clearKeyframeSelection();
    }

    restoreKeyframeData(data) {
        const source = this.getKeyframeSource();
        if (source && !source.includes(data)) source.push(data);
        this.selectKeyframe(data, getKeyframeFrame(data, source?.length ?? 0), source?.indexOf(data));
    }

    save() {
        console.log("Workspace saved.");
    }
}

function getPositionKey(data) {
    return ['frame', 'frameIndex', 'at'].find((key) => hasOwn(data, key));
}

function setMetadata(data, metadata) {
    if (metadata === undefined) delete data.metadata;
    else data.metadata = cloneValue(metadata);
}

function setDuration(workspace, data, duration) {
    if (data && hasOwn(data, 'duration')) data.duration = duration;
    else if (workspace.animation && hasOwn(workspace.animation, 'duration')) {
        workspace.animation.duration = duration;
    }
    workspace.duration = Number(duration) || 0;
}

function cloneValue(value) {
    if (value === undefined) return undefined;
    if (value === null || typeof value !== 'object') return value;
    return JSON.parse(JSON.stringify(value));
}

function getKeyframeFrame(keyframe, fallback) {
    if (typeof keyframe === 'number') return Math.round(keyframe);
    if (!keyframe || typeof keyframe !== 'object') return fallback;

    const position = keyframe.frame ?? keyframe.frameIndex ?? keyframe.at;
    const frame = Number(position);
    return Number.isFinite(frame) ? Math.round(frame) : fallback;
}

function hasOwn(object, key) {
    return Object.prototype.hasOwnProperty.call(object, key);
}

function getTotalFrames(data) {
    const candidates = [
        data?.totalFrames,
        data?.frameCount,
        data?.scene?.totalFrames,
        data?.scene?.frameCount,
        data?.animation?.totalFrames,
        data?.animation?.frameCount,
        data?.animation?.frames?.length,
        getKeyframeFrameCount(data?.animation?.keyframes),
        data?.frames?.length,
        data?.scene?.animation?.totalFrames,
        data?.scene?.animation?.frames?.length,
        getKeyframeFrameCount(data?.scene?.animation?.keyframes),
        data?.scene?.frames?.length,
    ];

    for (const value of candidates) {
        const frames = Number(value);
        if (Number.isInteger(frames) && frames > 0) return frames;
    }
    return 1;
}

function getKeyframeFrameCount(keyframes) {
    if (!Array.isArray(keyframes) || keyframes.length === 0) return 0;

    const positions = keyframes.map((keyframe, index) => {
        const position = keyframe?.frame ?? keyframe?.frameIndex ?? keyframe?.at;
        const frame = Number(position);
        return Number.isInteger(frame) && frame >= 0 ? frame : index;
    });
    return Math.max(...positions) + 1;
}

function getAnimation(data) {
    if (data?.animation && typeof data.animation === 'object') return data.animation;
    if (data?.scene?.animation && typeof data.scene.animation === 'object') {
        return data.scene.animation;
    }
    if (Array.isArray(data?.frames)) {
        return { frames: data.frames, duration: data.duration };
    }
    return null;
}

function getDuration(animation, data) {
    const duration = Number(animation?.duration ?? data?.duration ?? 0);
    return Number.isFinite(duration) && duration >= 0 ? duration : 0;
}

function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
}
