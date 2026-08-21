const DEFAULT_COLORS = Object.freeze([
    '#58c4dd', '#f0b429', '#d86b9b', '#7ac74f', '#9b8afb', '#ef8354',
]);

export class BehaviorTimeline {
    constructor(workspace) {
        this.workspace = workspace;
        this.container = null;
        this.filter = { query: '', labels: [], types: [] };
    }

    init(container) {
        this.container = container;
        this.render();
    }

    getEntries() {
        const rollout = this.workspace.rollout ?? this.workspace.data?.flygymRollout;
        const entries = rollout?.behaviors ?? this.workspace.data?.behaviors ?? [];
        return entries.map((entry, index) => normalizeEntry(entry, index));
    }

    getFilteredEntries() {
        const query = this.filter.query.trim().toLowerCase();
        return this.getEntries().filter((entry) => {
            if (this.filter.labels.length && !this.filter.labels.includes(entry.label)) return false;
            if (this.filter.types.length && !this.filter.types.includes(entry.type)) return false;
            return !query || `${entry.label} ${entry.type}`.toLowerCase().includes(query);
        });
    }

    setFilter(filter = {}) {
        this.filter = {
            query: String(filter.query ?? this.filter.query ?? ''),
            labels: Array.isArray(filter.labels) ? [...filter.labels] : this.filter.labels,
            types: Array.isArray(filter.types) ? [...filter.types] : this.filter.types,
        };
        this.workspace.behaviorFilter = { ...this.filter };
        this.render();
    }

    render() {
        if (!this.container) return;
        const entries = this.getFilteredEntries();
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        const currentFrame = this.workspace.currentFrame;
        this.container.innerHTML = `
            <section class="behavior-timeline-panel" aria-label="Behavior timeline">
                <div class="behavior-timeline-header">
                    <strong>Behavior Timeline</strong>
                    <input class="behavior-filter-input" type="search" placeholder="Filter behavior" aria-label="Filter behavior">
                    <span>${entries.length} marker(s)</span>
                </div>
                <div class="behavior-timeline-track">
                    <div class="behavior-current-indicator" style="left:${(currentFrame / Math.max(1, totalFrames - 1)) * 100}%"></div>
                    ${entries.map((entry) => renderEntry(entry, totalFrames)).join('')}
                </div>
            </section>
        `;
        const input = this.container.querySelector('.behavior-filter-input');
        input.value = this.filter.query;
        input.addEventListener('input', (event) => {
            this.filter.query = event.target.value;
            this.workspace.behaviorFilter = { ...this.filter };
            this.render();
        });
        this.container.querySelectorAll('.behavior-segment').forEach((segment) => {
            segment.addEventListener('click', () => {
                this.workspace.setFrame(Number(segment.dataset.startFrame));
            });
        });
    }

    updateFrame() {
        const indicator = this.container?.querySelector('.behavior-current-indicator');
        if (!indicator) return this.render();
        const totalFrames = Math.max(1, this.workspace.totalFrames);
        indicator.style.left = `${(this.workspace.currentFrame / Math.max(1, totalFrames - 1)) * 100}%`;
    }
}

function normalizeEntry(entry, index) {
    const startFrame = Math.max(0, Math.round(Number(entry.startFrame ?? entry.start_frame ?? entry.frame ?? 0)));
    const endFrame = Math.max(startFrame, Math.round(Number(entry.endFrame ?? entry.end_frame ?? entry.end ?? startFrame)));
    return {
        id: entry.id ?? `behavior-${index}`,
        type: entry.type ?? 'segment',
        label: entry.label ?? entry.name ?? 'unlabeled',
        color: validColor(entry.color)
            ? entry.color
            : DEFAULT_COLORS[index % DEFAULT_COLORS.length],
        startFrame,
        endFrame,
        metadata: entry.metadata ?? {},
    };
}

function renderEntry(entry, totalFrames) {
    const start = (entry.startFrame / Math.max(1, totalFrames - 1)) * 100;
    const width = Math.max(0.5, ((entry.endFrame - entry.startFrame) / Math.max(1, totalFrames - 1)) * 100);
    return `
        <button class="behavior-segment" type="button"
            title="${escapeAttribute(`${entry.label}: ${entry.startFrame}-${entry.endFrame}`)}"
            aria-label="${escapeAttribute(entry.label)}"
            style="left:${start}%;width:${width}%;background-color:${escapeAttribute(entry.color)}"
            data-start-frame="${entry.startFrame}" data-end-frame="${entry.endFrame}">
            <span>${escapeText(entry.label)}</span>
        </button>
    `;
}

function escapeText(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[character]));
}

function escapeAttribute(value) {
    return escapeText(value);
}

function validColor(value) {
    return typeof value === 'string' && /^(#[0-9a-f]{3,8}|[a-z]+)$/i.test(value);
}
