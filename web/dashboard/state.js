/** UI state for the integration shell. Scientific state remains in Workspace. */
export const DASHBOARD_TABS = Object.freeze([
    ['home', 'Home'],
    ['datasets', 'Datasets'],
    ['viewer', 'Viewer'],
    ['analysis', 'Analysis'],
    ['validation', 'Validation'],
    ['reports', 'Reports'],
    ['publication', 'Publication'],
    ['plugins', 'Plugins'],
    ['assistant', 'Assistant'],
]);

export class DashboardState {
    constructor(workspace) {
        this.workspace = workspace;
        this.activeTab = 'home';
        this.lastError = null;
        this.listeners = new Set();
    }

    onChange(listener) {
        if (typeof listener !== 'function') return () => {};
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    setTab(tab) {
        if (!DASHBOARD_TABS.some(([key]) => key === tab)) return this.activeTab;
        if (this.activeTab === tab) return tab;
        this.activeTab = tab;
        this.notify();
        return tab;
    }

    setError(error) {
        this.lastError = error ? String(error.message ?? error) : null;
        this.notify();
    }

    notify() {
        this.listeners.forEach((listener) => listener(this.snapshot()));
    }

    snapshot() {
        const workspace = this.workspace;
        return {
            activeTab: this.activeTab,
            currentFrame: workspace.currentFrame,
            totalFrames: workspace.totalFrames,
            currentTime: workspace.currentTime,
            playbackState: workspace.playbackState,
            selectedNode: workspace.selectedNode,
            selectedKeyframe: workspace.selectedKeyframe,
            datasetLoaded: Boolean(workspace.rollout || workspace.data?.nodes?.length || workspace.frames?.length),
            lastError: this.lastError,
        };
    }
}
