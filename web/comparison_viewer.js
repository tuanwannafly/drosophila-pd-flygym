export class RolloutComparisonViewer {
    constructor() {
        this.container = null;
        this.comparison = null;
        this.currentFrame = 0;
    }

    render(container, comparison) {
        this.container = container;
        this.comparison = comparison;
        if (!container) return;
        const conditions = comparison?.conditions ?? [];
        const maximumFrame = Math.max(0, ...conditions.map((condition) => Number(condition.rollout?.frameCount ?? 0) - 1));
        this.currentFrame = Math.min(this.currentFrame, maximumFrame);
        container.innerHTML = `
            <section class="comparison-viewer" aria-label="Rollout comparison">
                <div class="comparison-toolbar">
                    <strong>Rollout Comparison</strong>
                    <span class="comparison-current-frame">Frame 0</span>
                </div>
                <input class="comparison-frame-slider" type="range" min="0" max="${maximumFrame}" value="${this.currentFrame}" aria-label="Comparison frame">
                <div class="comparison-columns">
                    ${conditions.map((condition) => `
                        <article class="comparison-condition">
                            <h4>${escapeText(condition.label)}</h4>
                            <canvas class="comparison-canvas" data-condition="${conditions.indexOf(condition)}" width="320" height="160" aria-label="${escapeText(condition.label)} trajectory"></canvas>
                            <p>${condition.rollout?.frameCount ?? 0} frames</p>
                            <p>Speed: ${formatMetric(condition.statistics?.summary?.speed?.mean)}</p>
                            <p>Yaw rate: ${formatMetric(condition.statistics?.summary?.angularVelocity?.mean)}</p>
                        </article>
                    `).join('')}
                </div>
                <div class="comparison-differences">
                    ${(comparison?.differences ?? []).map((difference) => `
                        <div><strong>${escapeText(difference.label)}</strong> - error heatmap rows: ${difference.jointErrorHeatmap?.length ?? 0}</div>
                    `).join('')}
                </div>
            </section>
        `;
        const slider = container.querySelector('.comparison-frame-slider');
        slider?.addEventListener('input', () => this.setFrame(slider.value));
        this.drawCanvases();
    }

    setFrame(frame) {
        this.currentFrame = Math.max(0, Math.round(Number(frame) || 0));
        const readout = this.container?.querySelector('.comparison-current-frame');
        if (readout) readout.textContent = `Frame ${this.currentFrame}`;
        const slider = this.container?.querySelector('.comparison-frame-slider');
        if (slider) slider.value = String(this.currentFrame);
        this.drawCanvases();
    }

    drawCanvases() {
        const conditions = this.comparison?.conditions ?? [];
        this.container?.querySelectorAll('.comparison-canvas').forEach((canvas) => {
            const index = Number(canvas.dataset.condition);
            drawComparisonCanvas(canvas, conditions[index]?.rollout, this.currentFrame);
        });
    }
}

function formatMetric(value) {
    return Number.isFinite(Number(value)) ? Number(value).toFixed(4) : 'n/a';
}

function escapeText(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[character]));
}

function drawComparisonCanvas(canvas, rollout, frame) {
    const context = canvas?.getContext?.('2d');
    if (!context) return;
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = '#0b0b0b';
    context.fillRect(0, 0, canvas.width, canvas.height);
    const values = rollout?.channels?.thorax;
    const points = (Array.isArray(values) ? values : []).map(toPoint).filter(Boolean);
    if (!points.length) return;
    const xs = points.map((point) => point.x);
    const ys = points.map((point) => point.y);
    const minX = Math.min(...xs); const maxX = Math.max(...xs);
    const minY = Math.min(...ys); const maxY = Math.max(...ys);
    const project = (point) => ({
        x: 12 + ((point.x - minX) / Math.max(1e-9, maxX - minX)) * (canvas.width - 24),
        y: canvas.height - 12 - ((point.y - minY) / Math.max(1e-9, maxY - minY)) * (canvas.height - 24),
    });
    context.strokeStyle = '#58c4dd';
    context.lineWidth = 2;
    context.beginPath();
    points.forEach((point, index) => {
        const screen = project(point);
        if (index === 0) context.moveTo(screen.x, screen.y); else context.lineTo(screen.x, screen.y);
    });
    context.stroke();
    const current = project(points[Math.min(points.length - 1, Math.max(0, Number(frame) || 0))]);
    context.fillStyle = '#ffcc66';
    context.beginPath();
    context.arc(current.x, current.y, 5, 0, Math.PI * 2);
    context.fill();
}

function toPoint(value) {
    if (Array.isArray(value) && value.length >= 2) return { x: Number(value[0]), y: Number(value[1]) };
    const source = value?.position ?? value?.translation ?? value;
    if (!source) return null;
    const x = Number(source.x ?? source[0]); const y = Number(source.y ?? source[1]);
    return Number.isFinite(x) && Number.isFinite(y) ? { x, y } : null;
}

