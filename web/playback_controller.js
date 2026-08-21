import { WORKSPACE_EVENTS } from './workspace.js';

export const PLAYBACK_STATES = Object.freeze({
    STOPPED: 'Stopped',
    PAUSED: 'Paused',
    PLAYING: 'Playing',
});

export class PlaybackController {
    constructor(workspace, onChange = null) {
        this.workspace = workspace;
        this.onChange = onChange;
        this.animationFrameId = null;
        this.lastTimestamp = null;
        if (!Object.values(PLAYBACK_STATES).includes(this.workspace.playbackState)) {
            this.workspace.playbackState = PLAYBACK_STATES.STOPPED;
        }
    }

    play() {
        if (this.workspace.playbackState === PLAYBACK_STATES.PLAYING) {
            return this.workspace.playbackState;
        }
        return this.startPlaying();
    }

    pause() {
        this.cancelScheduler();
        return this.setState(PLAYBACK_STATES.PAUSED);
    }

    stop() {
        this.cancelScheduler();
        this.setTime(0);
        this.lastTimestamp = null;
        this.setState(PLAYBACK_STATES.STOPPED);
        this.notifyChange();
        return this.workspace.playbackState;
    }

    resume() {
        if (this.workspace.playbackState !== PLAYBACK_STATES.PAUSED) {
            return this.play();
        }
        return this.startPlaying();
    }

    setLoop(enabled) {
        this.workspace.loop = Boolean(enabled);
        return this.workspace.loop;
    }

    setFps(fps) {
        const value = Number(fps);
        if (!Number.isFinite(value) || value <= 0) return this.workspace.fps;
        this.workspace.fps = value;
        return this.workspace.fps;
    }

    setSpeed(speed) {
        const value = Number(speed);
        if (!Number.isFinite(value) || value <= 0) return this.workspace.speed;
        this.workspace.speed = value;
        return this.workspace.speed;
    }

    setReverse(reverse) {
        this.workspace.reverse = Boolean(reverse);
        return this.workspace.reverse;
    }

    stepForward() {
        this.pause();
        return this.advanceFrame(1);
    }

    stepBackward() {
        this.pause();
        return this.advanceFrame(-1);
    }

    startPlaying() {
        this.cancelScheduler();
        this.lastTimestamp = null;
        this.setState(PLAYBACK_STATES.PLAYING);
        this.notifyChange();
        this.schedule();
        return this.workspace.playbackState;
    }

    schedule() {
        if (this.workspace.playbackState !== PLAYBACK_STATES.PLAYING) return;
        if (typeof requestAnimationFrame !== 'function') return;
        this.animationFrameId = requestAnimationFrame((timestamp) => this.tick(timestamp));
    }

    tick(timestamp) {
        if (this.workspace.playbackState !== PLAYBACK_STATES.PLAYING) return;
        if (this.lastTimestamp === null) this.lastTimestamp = timestamp;
        const elapsed = Math.max(0, (timestamp - this.lastTimestamp) / 1000);
        this.lastTimestamp = timestamp;
        this.advanceTime(elapsed * this.workspace.speed * (this.workspace.reverse ? -1 : 1));
        if (this.workspace.playbackState === PLAYBACK_STATES.PLAYING) this.schedule();
    }

    advanceTime(delta) {
        const duration = this.getPlaybackDuration();
        let nextTime = this.workspace.currentTime + delta;
        let finished = false;

        if (nextTime >= duration || nextTime <= 0) {
            if (this.workspace.loop && duration > 0) {
                nextTime = nextTime >= duration
                    ? nextTime % duration
                    : duration + (nextTime % duration);
                this.workspace.emit(WORKSPACE_EVENTS.PLAYBACK_LOOPED, { time: nextTime });
            } else {
                nextTime = Math.min(duration, Math.max(0, nextTime));
                finished = true;
            }
        }

        this.setTime(nextTime);
        if (finished) {
            this.cancelScheduler();
            this.workspace.emit(WORKSPACE_EVENTS.PLAYBACK_FINISHED, { time: nextTime });
            this.setState(PLAYBACK_STATES.STOPPED);
        }
        this.notifyChange();
        return this.workspace.currentTime;
    }

    advanceFrame(delta) {
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        const nextFrame = clamp(this.workspace.currentFrame + delta, 0, totalFrames - 1);
        this.setFrame(nextFrame);
        this.notifyChange();
        return this.workspace.currentFrame;
    }

    setTime(time) {
        const duration = this.getPlaybackDuration();
        const nextTime = clamp(time, 0, duration);
        const frameDuration = this.getFrameDuration();
        const nextFrame = frameDuration > 0
            ? clamp(Math.round(nextTime / frameDuration), 0, Math.max(0, this.workspace.totalFrames - 1))
            : 0;
        this.workspace.setFrame(nextFrame, nextTime);
    }

    setFrame(frame) {
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        const nextFrame = clamp(frame, 0, totalFrames - 1);
        this.workspace.setFrame(nextFrame, nextFrame * this.getFrameDuration());
    }

    getFrameDuration() {
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        if (totalFrames <= 1) return 0;
        if (this.workspace.duration > 0) return this.workspace.duration / (totalFrames - 1);
        return 1 / Math.max(1, this.workspace.fps);
    }

    getPlaybackDuration() {
        const frameDuration = this.getFrameDuration();
        return this.workspace.duration > 0
            ? this.workspace.duration
            : Math.max(0, this.workspace.totalFrames - 1) * frameDuration;
    }

    cancelScheduler() {
        if (this.animationFrameId !== null && typeof cancelAnimationFrame === 'function') {
            cancelAnimationFrame(this.animationFrameId);
        }
        this.animationFrameId = null;
        this.lastTimestamp = null;
    }

    notifyChange() {
        if (this.onChange) this.onChange(this.workspace);
    }

    setState(state) {
        if (this.workspace.playbackState === state) return state;
        this.workspace.playbackState = state;
        const eventByState = {
            [PLAYBACK_STATES.PLAYING]: WORKSPACE_EVENTS.PLAYBACK_STARTED,
            [PLAYBACK_STATES.PAUSED]: WORKSPACE_EVENTS.PLAYBACK_PAUSED,
            [PLAYBACK_STATES.STOPPED]: WORKSPACE_EVENTS.PLAYBACK_STOPPED,
        };
        this.workspace.emit(eventByState[state], { state });
        return this.workspace.playbackState;
    }
}

function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
}
