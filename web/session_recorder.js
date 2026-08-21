import { WORKSPACE_EVENTS } from './workspace.js';

export class SessionRecorder {
    constructor(workspace) {
        this.workspace = workspace;
        this.events = [];
        this.active = false;
        this.unsubscribers = [];
    }

    start(metadata = {}) {
        this.stop();
        this.events = [{ type: 'SessionStarted', time: now(), metadata }];
        this.active = true;
        Object.values(WORKSPACE_EVENTS).forEach((eventName) => {
            this.unsubscribers.push(this.workspace.on(eventName, (event) => {
                this.record(eventName, sanitizeEvent(event));
            }));
        });
        return this.events[0];
    }

    stop() {
        if (!this.active) return this.events;
        this.record('SessionStopped', {});
        this.unsubscribers.splice(0).forEach((unsubscribe) => unsubscribe());
        this.active = false;
        return this.events;
    }

    record(type, payload = {}) {
        if (!this.active && type !== 'SessionStarted') return null;
        const event = { type, time: now(), payload };
        this.events.push(event);
        return event;
    }

    recordFrame(frame) {
        return this.record('PlaybackFrame', { frame });
    }

    recordCamera(camera) {
        return this.record('CameraChanged', sanitizeEvent(camera));
    }

    recordTimeline(timeline) {
        return this.record('TimelineChanged', sanitizeEvent(timeline));
    }

    export() {
        return {
            version: 1,
            scope: 'User-interface session recording; not scientific evidence.',
            events: this.events.map((event) => ({ ...event })),
        };
    }
}

function sanitizeEvent(value) {
    if (!value || typeof value !== 'object') return value;
    return Object.fromEntries(Object.entries(value).filter(([key]) => key !== 'workspace'));
}

function now() {
    return new Date().toISOString();
}

