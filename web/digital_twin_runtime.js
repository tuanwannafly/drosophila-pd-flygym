/**
 * Runtime state for an imported DigitalFly3D or pose-frame stream.
 *
 * This module owns computational playback state only. It does not load files,
 * run simulation code, or make biological inferences. Interpolated frames are
 * explicitly marked and are created only between supplied frames.
 */

export const TWIN_PLAYBACK_STATES = Object.freeze({
    STOPPED: 'Stopped',
    PAUSED: 'Paused',
    PLAYING: 'Playing',
});

const FRAME_EVENTS = Object.freeze({
    FRAME_CHANGED: 'frame_changed',
    STATE_CHANGED: 'state_changed',
    PLAYBACK_CHANGED: 'playback_changed',
    RESET: 'reset',
});

export class DigitalTwinRuntime {
    constructor({ model = null, fps = 60, historyLimit = 120, predictionHooks = {} } = {}) {
        this.model = model;
        this.fps = positiveNumber(fps, 60);
        this.historyLimit = Math.max(1, Math.trunc(Number(historyLimit) || 120));
        this.predictionHooks = predictionHooks && typeof predictionHooks === 'object' ? predictionHooks : {};
        this.frames = new Map();
        this.frameCache = new Map();
        this.trajectoryCache = new Map();
        this.history = [];
        this.predictionBuffer = [];
        this.state = emptyState();
        this.currentFrame = 0;
        this.playbackState = TWIN_PLAYBACK_STATES.STOPPED;
        this.speed = 1;
        this.reverse = false;
        this.loop = false;
        this.listeners = new Map();
        this.animationFrameId = null;
        this.lastTimestamp = null;
        this.frameAccumulator = 0;

        if (model?.fly?.trajectories?.list) {
            this.frameCount = inferModelFrameCount(model);
        } else {
            this.frameCount = 0;
        }
    }

    get totalFrames() {
        return this.frames.size > 0 ? this.frames.size : this.frameCount;
    }

    get isPlaying() {
        return this.playbackState === TWIN_PLAYBACK_STATES.PLAYING;
    }

    on(eventName, listener) {
        if (typeof listener !== 'function') return () => {};
        const listeners = this.listeners.get(eventName) ?? new Set();
        listeners.add(listener);
        this.listeners.set(eventName, listeners);
        return () => this.off(eventName, listener);
    }

    onChange(listener) { return this.on('*', listener); }

    off(eventName, listener) {
        this.listeners.get(eventName)?.delete(listener);
    }

    append_frame(frame) {
        const supplied = clone(frame);
        if (!supplied || typeof supplied !== 'object' || Array.isArray(supplied)) {
            throw new TypeError('A frame object is required.');
        }
        const explicitIndex = supplied.frame_index ?? supplied.frame;
        const frameIndex = explicitIndex === undefined
            ? nextFrameIndex(this.frames)
            : Number(explicitIndex);
        if (!Number.isInteger(frameIndex) || frameIndex < 0) {
            throw new RangeError('frame_index must be a non-negative integer.');
        }
        supplied.frame_index = frameIndex;
        this.frames.set(frameIndex, supplied);
        this.frameCount = Math.max(this.frameCount, frameIndex + 1);
        this.frameCache.clear();
        this.trajectoryCache.clear();
        if (this.frames.size === 1) this.seek(frameIndex);
        return clone(supplied);
    }

    appendFrame(frame) { return this.append_frame(frame); }

    append_frames(frames = []) {
        if (!Array.isArray(frames)) throw new TypeError('frames must be an array.');
        return frames.map((frame) => this.append_frame(frame));
    }

    appendFrames(frames = []) { return this.append_frames(frames); }

    update(frame = this.currentFrame) {
        return this.seek(frame);
    }

    seek(frame = 0) {
        const target = this._clampFrame(Number(frame));
        const resolved = this._resolveFrame(target);
        this.currentFrame = target;
        this.state = stateFromFrame(resolved.frame, target, resolved.interpolated, resolved.sourceFrames);
        if (this.model?.updateFrame && Number.isInteger(target)) {
            this.model.updateFrame(target);
        }
        this._recordHistory();
        this.emit(FRAME_EVENTS.FRAME_CHANGED, {
            frame: target,
            state: this.getState(),
            interpolated: resolved.interpolated,
            sourceFrames: resolved.sourceFrames,
        });
        return this.getState();
    }

    reset() {
        this._cancelScheduler();
        this.playbackState = TWIN_PLAYBACK_STATES.STOPPED;
        this.currentFrame = this._firstFrameIndex();
        this.history = [];
        this.frameCache.clear();
        this.predictionBuffer = [];
        if (this.totalFrames > 0) this.seek(this.currentFrame);
        else this.state = emptyState();
        this.emit(FRAME_EVENTS.RESET, { state: this.getState() });
        this.emit(FRAME_EVENTS.PLAYBACK_CHANGED, { playbackState: this.playbackState });
        return this.getState();
    }

    clear() {
        this._cancelScheduler();
        this.frames.clear();
        this.frameCache.clear();
        this.trajectoryCache.clear();
        this.history = [];
        this.predictionBuffer = [];
        this.frameCount = 0;
        this.currentFrame = 0;
        this.state = emptyState();
        this.playbackState = TWIN_PLAYBACK_STATES.STOPPED;
        this.emit(FRAME_EVENTS.RESET, { state: this.getState() });
    }

    getState() {
        return clone(this.state);
    }

    getFrame(frame = this.currentFrame) {
        return clone(this._resolveFrame(this._clampFrame(Number(frame))).frame);
    }

    appendPrediction(frame) {
        const value = clone(frame);
        if (!value || typeof value !== 'object' || Array.isArray(value)) {
            throw new TypeError('A prediction frame object is required.');
        }
        this.predictionBuffer.push(value);
        return clone(value);
    }

    clearPredictionBuffer() {
        this.predictionBuffer = [];
    }

    getTrajectory(channel = 'position') {
        const key = String(channel);
        if (this.trajectoryCache.has(key)) return clone(this.trajectoryCache.get(key));
        const values = [...this.frames.keys()].sort((left, right) => left - right).map((index) => {
            const frame = this.frames.get(index);
            return { frame_index: index, value: clone(frame?.[key]) };
        }).filter((entry) => entry.value !== undefined && entry.value !== null);
        this.trajectoryCache.set(key, values);
        return clone(values);
    }

    play() {
        if (this.totalFrames <= 1) return this.setPlaybackState(TWIN_PLAYBACK_STATES.STOPPED);
        this.lastTimestamp = null;
        this.frameAccumulator = 0;
        this.setPlaybackState(TWIN_PLAYBACK_STATES.PLAYING);
        this._schedule();
        return this.playbackState;
    }

    pause() {
        this._cancelScheduler();
        return this.setPlaybackState(TWIN_PLAYBACK_STATES.PAUSED);
    }

    resume() { return this.play(); }

    stop() {
        this._cancelScheduler();
        this.setPlaybackState(TWIN_PLAYBACK_STATES.STOPPED);
        this.seek(this._firstFrameIndex());
        return this.playbackState;
    }

    setPlaybackState(state) {
        if (!Object.values(TWIN_PLAYBACK_STATES).includes(state)) {
            throw new RangeError(`Unknown playback state: ${state}`);
        }
        this.playbackState = state;
        this.emit(FRAME_EVENTS.PLAYBACK_CHANGED, { playbackState: state });
        return state;
    }

    setSpeed(speed) {
        this.speed = positiveNumber(speed, this.speed);
        return this.speed;
    }

    setLoop(enabled) {
        this.loop = Boolean(enabled);
        return this.loop;
    }

    setReverse(enabled) {
        this.reverse = Boolean(enabled);
        return this.reverse;
    }

    tick(timestamp) {
        if (!this.isPlaying) return this.currentFrame;
        if (this.lastTimestamp === null) this.lastTimestamp = Number(timestamp) || 0;
        const elapsed = Math.max(0, (Number(timestamp) - this.lastTimestamp) / 1000);
        this.lastTimestamp = Number(timestamp);
        this.frameAccumulator += elapsed * this.fps * this.speed * (this.reverse ? -1 : 1);
        const next = this.currentFrame + this.frameAccumulator;
        this.frameAccumulator = 0;
        const maximum = Math.max(0, this._lastFrameIndex());
        if (next > maximum || next < this._firstFrameIndex()) {
            if (this.loop && this.totalFrames > 1) {
                this.currentFrame = next > maximum ? this._firstFrameIndex() : maximum;
                this.frameAccumulator = next > maximum ? next - maximum - 1 : next - this._firstFrameIndex();
                this.emit(FRAME_EVENTS.PLAYBACK_CHANGED, { event: 'looped', playbackState: this.playbackState });
            } else {
                this.currentFrame = next > maximum ? maximum : this._firstFrameIndex();
                this.seek(this.currentFrame);
                this._cancelScheduler();
                this.setPlaybackState(TWIN_PLAYBACK_STATES.STOPPED);
                return this.currentFrame;
            }
        } else {
            this.seek(next);
        }
        this._schedule();
        return this.currentFrame;
    }

    predict_next_frame(...args) {
        return typeof this.predictionHooks.predict_next_frame === 'function'
            ? this.predictionHooks.predict_next_frame(this.getState(), ...args)
            : null;
    }

    estimate_state(...args) {
        return typeof this.predictionHooks.estimate_state === 'function'
            ? this.predictionHooks.estimate_state(this.getState(), ...args)
            : null;
    }

    emit(eventName, detail = {}) {
        const event = { type: eventName, runtime: this, ...detail };
        this.listeners.get(eventName)?.forEach((listener) => listener(event));
        this.listeners.get('*')?.forEach((listener) => listener(event));
    }

    _resolveFrame(target) {
        if (this.frames.size === 0) {
            if (this.model?.updateFrame) return { frame: this.model.updateFrame(Math.round(target)), interpolated: false, sourceFrames: [] };
            return { frame: {}, interpolated: false, sourceFrames: [] };
        }
        const exact = this.frames.get(target);
        if (exact) return { frame: exact, interpolated: false, sourceFrames: [target] };
        const indices = [...this.frames.keys()].sort((left, right) => left - right);
        const lower = indices.filter((index) => index < target).pop();
        const upper = indices.find((index) => index > target);
        if (lower === undefined) return { frame: this.frames.get(indices[0]), interpolated: false, sourceFrames: [indices[0]] };
        if (upper === undefined) return { frame: this.frames.get(indices.at(-1)), interpolated: false, sourceFrames: [indices.at(-1)] };
        if (this.frameCache.has(target)) {
            return { frame: this.frameCache.get(target), interpolated: true, sourceFrames: [lower, upper] };
        }
        const amount = (target - lower) / (upper - lower);
        const frame = interpolateFrame(this.frames.get(lower), this.frames.get(upper), amount, target);
        this.frameCache.set(target, frame);
        return { frame, interpolated: true, sourceFrames: [lower, upper] };
    }

    _recordHistory() {
        this.history.push({ frame: this.currentFrame, state: this.getState() });
        if (this.history.length > this.historyLimit) this.history.splice(0, this.history.length - this.historyLimit);
    }

    _clampFrame(frame) {
        const value = Number.isFinite(frame) ? frame : 0;
        return Math.min(this._lastFrameIndex(), Math.max(this._firstFrameIndex(), value));
    }

    _firstFrameIndex() {
        return this.frames.size ? Math.min(...this.frames.keys()) : 0;
    }

    _lastFrameIndex() {
        return this.frames.size ? Math.max(...this.frames.keys()) : Math.max(0, this.frameCount - 1);
    }

    _schedule() {
        if (!this.isPlaying || this.animationFrameId !== null) return;
        if (typeof requestAnimationFrame === 'function') {
            this.animationFrameId = requestAnimationFrame((timestamp) => {
                this.animationFrameId = null;
                this.tick(timestamp);
            });
        }
    }

    _cancelScheduler() {
        if (this.animationFrameId !== null && typeof cancelAnimationFrame === 'function') {
            cancelAnimationFrame(this.animationFrameId);
        }
        this.animationFrameId = null;
        this.lastTimestamp = null;
    }
}

function stateFromFrame(frame, frameIndex, interpolated, sourceFrames) {
    const source = frame && typeof frame === 'object' ? frame : {};
    return {
        frame: frameIndex,
        pose: clone(source.pose ?? source),
        velocity: clone(source.velocity ?? source.joint_velocity ?? null),
        acceleration: clone(source.acceleration ?? source.joint_acceleration ?? null),
        joint: clone(source.joint ?? source.joint_angles ?? null),
        COM: clone(source.COM ?? source.com ?? null),
        orientation: clone(source.orientation ?? null),
        interpolated: Boolean(interpolated),
        sourceFrames: [...sourceFrames],
    };
}

function interpolateFrame(first, second, amount, frameIndex) {
    const result = interpolateValue(first, second, amount, '');
    if (!result || typeof result !== 'object' || Array.isArray(result)) return { frame_index: frameIndex, value: result };
    result.frame_index = frameIndex;
    result.interpolated = true;
    return result;
}

function interpolateValue(first, second, amount, key) {
    if (typeof first === 'number' && typeof second === 'number' && Number.isFinite(first) && Number.isFinite(second)) {
        return first + (second - first) * amount;
    }
    if (isQuaternionKey(key) && isNumericArray(first, 4) && isNumericArray(second, 4)) {
        return slerp(first, second, amount);
    }
    if (isNumericArray(first) && isNumericArray(second) && first.length === second.length) {
        return first.map((value, index) => interpolateValue(value, second[index], amount, key));
    }
    if (first && second && typeof first === 'object' && typeof second === 'object' && !Array.isArray(first) && !Array.isArray(second)) {
        const result = {};
        new Set([...Object.keys(first), ...Object.keys(second)]).forEach((name) => {
            if (first[name] === undefined) result[name] = clone(second[name]);
            else if (second[name] === undefined) result[name] = clone(first[name]);
            else result[name] = interpolateValue(first[name], second[name], amount, name);
        });
        return result;
    }
    return clone(amount < 1 ? first : second);
}

function slerp(first, second, amount) {
    let left = normalizeQuaternion(first);
    let right = normalizeQuaternion(second);
    let dot = left.reduce((sum, value, index) => sum + value * right[index], 0);
    if (dot < 0) { right = right.map((value) => -value); dot = -dot; }
    if (dot > 0.9995) return normalizeQuaternion(left.map((value, index) => value + (right[index] - value) * amount));
    const theta = Math.acos(Math.min(1, Math.max(-1, dot)));
    const sine = Math.sin(theta);
    const leftWeight = Math.sin((1 - amount) * theta) / sine;
    const rightWeight = Math.sin(amount * theta) / sine;
    return normalizeQuaternion(left.map((value, index) => value * leftWeight + right[index] * rightWeight));
}

function normalizeQuaternion(value) {
    const length = Math.hypot(...value);
    return length > 1e-12 ? value.map((item) => item / length) : [0, 0, 0, 1];
}

function isQuaternionKey(key) {
    const normalized = String(key).toLowerCase();
    return normalized.includes('orientation') || normalized.includes('quaternion') || normalized === 'rotation';
}

function isNumericArray(value, length = null) {
    return Array.isArray(value)
        && (length === null || value.length === length)
        && value.every((item) => typeof item === 'number' && Number.isFinite(item));
}

function emptyState() {
    return { frame: 0, pose: null, velocity: null, acceleration: null, joint: null, COM: null, orientation: null, interpolated: false, sourceFrames: [] };
}

function inferModelFrameCount(model) {
    return Math.max(0, ...(model.fly.trajectories.list() ?? []).map((record) => seriesLength(record.data)));
}

function seriesLength(value) {
    if (Array.isArray(value)) return value.length;
    if (value && typeof value === 'object') return Array.isArray(value.frames) ? value.frames.length : Array.isArray(value.values) ? value.values.length : 0;
    return 0;
}

function nextFrameIndex(frames) {
    return frames.size ? Math.max(...frames.keys()) + 1 : 0;
}

function positiveNumber(value, fallback) {
    const number = Number(value);
    return Number.isFinite(number) && number > 0 ? number : fallback;
}

function clone(value) {
    return value === undefined ? undefined : JSON.parse(JSON.stringify(value));
}

export { FRAME_EVENTS };
