const STORAGE_PREFIX = 'fly-studio:';

export class WorkspacePersistence {
    constructor(workspace, storage = globalThis.localStorage, experimentWorkspace = null) {
        this.workspace = workspace;
        this.storage = storage;
        this.experimentWorkspace = experimentWorkspace;
        this.autosaveId = null;
    }

    save(key = 'autosave') {
        const snapshot = serializeWorkspace(this.workspace, this.experimentWorkspace);
        this.storage?.setItem(this.storageKey(key), JSON.stringify(snapshot));
        return snapshot;
    }

    restore(key = 'autosave') {
        const text = this.storage?.getItem(this.storageKey(key));
        if (!text) return null;
        const snapshot = JSON.parse(text);
        if (!snapshot || snapshot.version !== 1 || !snapshot.data) {
            throw new Error('Unsupported Fly Studio workspace snapshot.');
        }
        this.workspace.load(snapshot.data);
        this.workspace.rollout = snapshot.rollout ?? this.workspace.rollout;
        this.workspace.rolloutStatistics = this.workspace.rollout?.statistics ?? null;
        this.workspace.setFrame(snapshot.currentFrame ?? 0, snapshot.currentTime ?? 0);
        this.workspace.fps = snapshot.fps ?? this.workspace.fps;
        this.workspace.speed = snapshot.speed ?? this.workspace.speed;
        this.workspace.loop = Boolean(snapshot.loop);
        this.workspace.reverse = Boolean(snapshot.reverse);
        this.workspace.trajectorySettings = {
            ...this.workspace.trajectorySettings,
            ...(snapshot.trajectorySettings ?? {}),
        };
        if (this.experimentWorkspace && snapshot.experimentWorkspace) {
            this.experimentWorkspace.restore(snapshot.experimentWorkspace);
        }
        return snapshot;
    }

    startAutosave(intervalMs = 10000, key = 'autosave') {
        this.stopAutosave();
        this.autosaveId = setInterval(() => this.save(key), intervalMs);
        return this.autosaveId;
    }

    stopAutosave() {
        if (this.autosaveId !== null) clearInterval(this.autosaveId);
        this.autosaveId = null;
    }

    addRecentFile(file) {
        return this.updateRecent('files', file);
    }

    addRecentSession(session) {
        return this.updateRecent('sessions', session);
    }

    getRecentFiles() {
        return this.getRecent('files');
    }

    getRecentSessions() {
        return this.getRecent('sessions');
    }

    storageKey(key) {
        return `${STORAGE_PREFIX}${key}`;
    }

    getRecent(kind) {
        try {
            const value = JSON.parse(this.storage?.getItem(this.storageKey(`recent-${kind}`)) ?? '[]');
            return Array.isArray(value) ? value : [];
        } catch (error) {
            return [];
        }
    }

    updateRecent(kind, value) {
        const items = [value, ...this.getRecent(kind).filter((item) => JSON.stringify(item) !== JSON.stringify(value))].slice(0, 10);
        this.storage?.setItem(this.storageKey(`recent-${kind}`), JSON.stringify(items));
        return items;
    }
}

export function serializeWorkspace(workspace, experimentWorkspace = null) {
    return {
        version: 1,
        savedAt: new Date().toISOString(),
        data: workspace.data,
        rollout: serializeRollout(workspace.rollout),
        currentFrame: workspace.currentFrame,
        currentTime: workspace.currentTime,
        fps: workspace.fps,
        speed: workspace.speed,
        loop: workspace.loop,
        reverse: workspace.reverse,
        trajectorySettings: workspace.trajectorySettings,
        experimentWorkspace: experimentWorkspace?.toJSON?.() ?? null,
        scope: 'Workspace state and loaded data only; not scientific evidence.',
    };
}

function serializeRollout(rollout) {
    if (!rollout) return null;
    const { workspaceData, ...serializable } = rollout;
    return serializable;
}
