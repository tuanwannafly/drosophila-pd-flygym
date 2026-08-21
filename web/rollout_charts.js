const CHART_COLORS = Object.freeze(['#58c4dd', '#f0b429', '#7ac74f', '#d86b9b', '#9b8afb']);

export class RolloutChartRenderer {
    constructor() {
        this.cache = new Map();
    }

    render(type, target, rollout, options = {}) {
        const series = seriesFor(type, rollout, options);
        const canvas = resolveCanvas(target);
        if (!canvas) return { rendered: false, reason: 'Canvas target unavailable' };
        const key = `${type}:${series.length}:${canvas.width}:${canvas.height}:${options.cacheKey ?? ''}`;
        if (this.cache.get(canvas) === key) return { rendered: true, cached: true, canvas };
        const context = canvas.getContext('2d');
        if (!context) return { rendered: false, reason: '2D context unavailable' };
        drawChart(context, canvas, series, options.title ?? type);
        this.cache.set(canvas, key);
        return { rendered: true, cached: false, canvas };
    }

    renderAll(targets, rollout, options = {}) {
        return Object.fromEntries(Object.entries(targets ?? {}).map(([type, target]) => [
            type,
            this.render(type, target, rollout, options[type] ?? {}),
        ]));
    }

    clear(target) {
        const canvas = resolveCanvas(target);
        if (!canvas) return;
        canvas.getContext('2d')?.clearRect(0, 0, canvas.width, canvas.height);
        this.cache.delete(canvas);
    }
}

export function chartToSVG(type, rollout, options = {}) {
    const series = seriesFor(type, rollout, options);
    const width = Number(options.width ?? 640);
    const height = Number(options.height ?? 240);
    const plot = chartGeometry(width, height, series);
    const lines = series.map((entry, index) => {
        const points = entry.values.map((value, pointIndex) => `${
            plot.left + (pointIndex / Math.max(1, entry.values.length - 1)) * plot.width
        },${plot.top + plot.height - normalize(value, plot.min, plot.max) * plot.height}`).join(' ');
        return `<polyline fill="none" stroke="${entry.color ?? CHART_COLORS[index % CHART_COLORS.length]}" stroke-width="2" points="${points}"/>`;
    }).join('');
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}"><rect width="100%" height="100%" fill="#111a22"/><text x="16" y="22" fill="#d8dee5" font-family="sans-serif" font-size="14">${escapeXml(options.title ?? type)}</text>${lines}</svg>`;
}

function seriesFor(type, rollout, options) {
    const statistics = rollout?.statistics ?? {};
    const timeseries = statistics.timeseries ?? {};
    const channels = rollout?.channels ?? {};
    if (type === 'velocity') return [{ label: 'speed', values: timeseries.speed ?? [], color: CHART_COLORS[0] }];
    if (type === 'angular') return [{ label: 'angular velocity', values: timeseries.angularVelocity ?? [], color: CHART_COLORS[1] }];
    if (type === 'joint') return namedSeries(channels.joint, options.limit ?? 6);
    if (type === 'com') return [{ label: 'COM x', values: (channels.com ?? []).map((item) => item.x), color: CHART_COLORS[2] }];
    if (type === 'timeline') return [{ label: 'frame', values: Array.from({ length: rollout?.frameCount ?? 0 }, (_, index) => index), color: CHART_COLORS[0] }];
    if (type === 'behavior') return [{ label: 'behavior', values: (rollout?.behaviors ?? []).map((entry) => entry.startFrame), color: CHART_COLORS[3] }];
    return [];
}

function namedSeries(value, limit) {
    if (!value || typeof value !== 'object') return [];
    return Object.entries(value).slice(0, limit).map(([label, series], index) => ({
        label,
        values: (series ?? []).map((item) => Number(item?.value ?? item?.x ?? item)).filter(Number.isFinite),
        color: CHART_COLORS[index % CHART_COLORS.length],
    }));
}

function resolveCanvas(target) {
    if (!target) return null;
    if (typeof HTMLCanvasElement !== 'undefined' && target instanceof HTMLCanvasElement) return target;
    if (target.querySelector) {
        const existing = target.querySelector('canvas');
        if (existing) return existing;
        const canvas = document.createElement('canvas');
        canvas.width = target.clientWidth || 640;
        canvas.height = target.clientHeight || 240;
        target.replaceChildren(canvas);
        return canvas;
    }
    return null;
}

function drawChart(context, canvas, series, title) {
    const geometry = chartGeometry(canvas.width, canvas.height, series);
    context.fillStyle = '#111a22';
    context.fillRect(0, 0, canvas.width, canvas.height);
    context.fillStyle = '#d8dee5';
    context.font = '14px sans-serif';
    context.fillText(title, 16, 22);
    context.strokeStyle = '#34434f';
    context.strokeRect(geometry.left, geometry.top, geometry.width, geometry.height);
    series.forEach((entry, index) => {
        if (!entry.values.length) return;
        context.strokeStyle = entry.color ?? CHART_COLORS[index % CHART_COLORS.length];
        context.lineWidth = 2;
        context.beginPath();
        entry.values.forEach((value, pointIndex) => {
            const x = geometry.left + (pointIndex / Math.max(1, entry.values.length - 1)) * geometry.width;
            const y = geometry.top + geometry.height - normalize(value, geometry.min, geometry.max) * geometry.height;
            if (pointIndex === 0) context.moveTo(x, y); else context.lineTo(x, y);
        });
        context.stroke();
    });
}

function chartGeometry(width, height, series) {
    const values = series.flatMap((entry) => entry.values).filter(Number.isFinite);
    const min = values.length ? Math.min(...values) : 0;
    const max = values.length ? Math.max(...values) : 1;
    return { left: 42, top: 34, width: Math.max(1, width - 56), height: Math.max(1, height - 52), min, max };
}

function normalize(value, min, max) {
    const number = Number(value);
    if (!Number.isFinite(number) || max <= min) return 0.5;
    return (number - min) / (max - min);
}

function escapeXml(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;',
    }[character]));
}

