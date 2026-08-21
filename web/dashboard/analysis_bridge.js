/** Reuses the existing chart and behavior renderers for synchronized updates. */
export class AnalysisBridge {
    constructor({ workspace, chartRenderer, behaviorTimeline }) {
        this.workspace = workspace;
        this.chartRenderer = chartRenderer;
        this.behaviorTimeline = behaviorTimeline;
        this.chartRoot = null;
    }

    attach(chartRoot) {
        this.chartRoot = chartRoot;
    }

    render() {
        if (!this.chartRoot) return;
        if (!this.workspace.rollout) {
            if (!this.chartRoot.children.length) this.chartRoot.textContent = 'No analysis data loaded.';
            return;
        }
        const targets = Object.fromEntries([...this.chartRoot.querySelectorAll('[data-chart]')]
            .map((element) => [element.dataset.chart, element]));
        this.chartRenderer?.renderAll(targets, this.workspace.rollout, { cacheKey: this.workspace.currentFrame });
        this.syncFrame(this.workspace.currentFrame);
    }

    syncFrame(frame = this.workspace.currentFrame) {
        this.behaviorTimeline?.updateFrame?.();
        if (!this.chartRoot) return;
        this.chartRoot.dataset.currentFrame = String(frame);
        this.chartRoot.querySelectorAll('[data-chart]').forEach((slot) => {
            slot.dataset.currentFrame = String(frame);
            slot.setAttribute('aria-label', `${slot.dataset.chart} chart, current frame ${frame}`);
            let marker = slot.querySelector('.digital-laboratory-chart-frame');
            if (!marker) {
                marker = document.createElement('span');
                marker.className = 'digital-laboratory-chart-frame';
                marker.setAttribute('aria-hidden', 'true');
                slot.append(marker);
            }
            const maximum = Math.max(1, this.workspace.totalFrames - 1);
            marker.style.left = `${Math.min(100, Math.max(0, Number(frame) / maximum * 100))}%`;
        });
    }
}
