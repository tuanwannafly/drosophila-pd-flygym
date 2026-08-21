import { WORKSPACE_EVENTS } from '../workspace.js';

const EVENT_NAMES = Object.freeze({
    [WORKSPACE_EVENTS.FRAME_CHANGED]: 'frame-changed',
    [WORKSPACE_EVENTS.PLAYBACK_STARTED]: 'playback-started',
    [WORKSPACE_EVENTS.PLAYBACK_PAUSED]: 'playback-paused',
    [WORKSPACE_EVENTS.PLAYBACK_STOPPED]: 'playback-stopped',
    [WORKSPACE_EVENTS.PLAYBACK_LOOPED]: 'playback-looped',
    [WORKSPACE_EVENTS.PLAYBACK_FINISHED]: 'playback-finished',
});

/** Adapts Workspace events to stable dashboard event names. */
export class WorkspaceSync {
    constructor(workspace, eventBus) {
        this.workspace = workspace;
        this.eventBus = eventBus;
        this.unsubscribers = [];
    }

    start() {
        if (this.unsubscribers.length) return;
        Object.entries(EVENT_NAMES).forEach(([workspaceEvent, dashboardEvent]) => {
            const unsubscribe = this.workspace.on(workspaceEvent, (event) => {
                this.eventBus.emit(`workspace:${dashboardEvent}`, event);
                this.eventBus.emit('workspace:changed', event);
            });
            this.unsubscribers.push(unsubscribe);
        });
    }

    stop() {
        this.unsubscribers.splice(0).forEach((unsubscribe) => unsubscribe());
    }
}
