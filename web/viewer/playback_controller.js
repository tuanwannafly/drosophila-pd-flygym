/** Playback state boundary. Scheduling is intentionally left to a later phase. */

export const PLAYBACK_STATES = Object.freeze(['stopped', 'paused', 'playing']);

export class ViewerPlaybackController {
    constructor() {
        this.state = 'stopped';
        this.listeners = new Set();
    }

    onChange(listener) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    setState(state) {
        if (!PLAYBACK_STATES.includes(state)) throw new RangeError(`Unknown playback state: ${state}`);
        this.state = state;
        this.listeners.forEach((listener) => listener(state));
        return state;
    }

    play() { return this.setState('playing'); }
    pause() { return this.setState('paused'); }
    stop() { return this.setState('stopped'); }
}
