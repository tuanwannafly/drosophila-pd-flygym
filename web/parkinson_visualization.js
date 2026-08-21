export function renderAnalyticsSVG(type, payload = {}, options = {}) {
    const width = Number(options.width ?? 640);
    const height = Number(options.height ?? 360);
    const title = escapeText(options.title ?? type);
    const body = type === 'trajectory' || type === 'trajectoryOverlay'
        ? trajectorySVG(payload, width, height)
        : type === 'scatter'
            ? scatterSVG(payload.points ?? payload, width, height)
            : type === 'featureImportance'
                ? importanceSVG(payload.features ?? payload, width, height)
                : type === 'distribution'
                    ? histogramSVG(payload.bins ?? payload.histogram ?? [], width, height)
        : type === 'correlation'
            ? matrixSVG(payload.matrix ?? [], width, height)
            : type === 'heatmap'
                ? matrixSVG(payload.matrix ?? [], width, height)
                : lineSVG(payload.values ?? payload.series ?? [], width, height);
    return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${title}"><rect width="100%" height="100%" fill="#1e1e1e"/><text x="16" y="24" fill="#cccccc">${title}</text>${body}</svg>`;
}

export class AnalyticsVisualizer {
    render(container, type, payload, options = {}) {
        if (!container) return renderAnalyticsSVG(type, payload, options);
        container.innerHTML = renderAnalyticsSVG(type, payload, options);
        return container.firstElementChild;
    }

    renderCanvas(canvas, type, payload, options = {}) {
        if (!canvas?.getContext) throw new Error('A CanvasRenderingContext2D is required.');
        const context = canvas.getContext('2d');
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.fillStyle = '#1e1e1e';
        context.fillRect(0, 0, canvas.width, canvas.height);
        context.fillStyle = '#cccccc';
        context.font = '14px sans-serif';
        context.fillText(options.title ?? type, 16, 24);
        const values = (payload.values ?? payload.series ?? []).map(Number).filter(Number.isFinite);
        drawLine(context, values, canvas.width, canvas.height);
        return canvas;
    }
}

function lineSVG(values, width, height) {
    const numbers = Array.isArray(values) ? values.map(Number).filter(Number.isFinite) : [];
    if (!numbers.length) return '<text x="16" y="52" fill="#808080">No finite data</text>';
    const min = Math.min(...numbers); const max = Math.max(...numbers); const range = max - min || 1;
    const points = numbers.map((value, index) => `${16 + (index / Math.max(1, numbers.length - 1)) * (width - 32)},${height - 20 - ((value - min) / range) * (height - 60)}`).join(' ');
    return `<polyline points="${points}" fill="none" stroke="#58c4dd" stroke-width="2"/>`;
}

function trajectorySVG(payload, width, height) {
    const series = Array.isArray(payload) ? payload : payload.trajectory ?? payload.trajectories?.[0] ?? [];
    const points = series.map((item) => [Number(item.x), Number(item.y)]).filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
    if (!points.length) return '<text x="16" y="52" fill="#808080">No finite trajectory</text>';
    const xs = points.map(([x]) => x); const ys = points.map(([, y]) => y);
    const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
    const scaleX = (width - 32) / (maxX - minX || 1); const scaleY = (height - 60) / (maxY - minY || 1);
    const path = points.map(([x, y]) => `${16 + (x - minX) * scaleX},${height - 20 - (y - minY) * scaleY}`).join(' ');
    return `<polyline points="${path}" fill="none" stroke="#f0a45d" stroke-width="2"/>`;
}

function matrixSVG(matrix, width, height) {
    const rows = Array.isArray(matrix) ? matrix : [];
    if (!rows.length) return '<text x="16" y="52" fill="#808080">No matrix data</text>';
    const size = Math.min(rows.length, 20); const cell = Math.min((width - 32) / size, (height - 60) / size);
    return rows.slice(0, size).map((row, y) => (row ?? []).slice(0, size).map((value, x) => `<rect x="${16 + x * cell}" y="${36 + y * cell}" width="${cell}" height="${cell}" fill="${heatColor(Number(value))}"/>`).join('')).join('');
}

function scatterSVG(points, width, height) {
    const values = (Array.isArray(points) ? points : []).map((point) => [Number(point.x), Number(point.y)]).filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y));
    if (!values.length) return '<text x="16" y="52" fill="#808080">No finite scatter data</text>';
    const xs = values.map(([x]) => x); const ys = values.map(([, y]) => y);
    const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys);
    return values.map(([x, y]) => `<circle cx="${16 + ((x - minX) / (maxX - minX || 1)) * (width - 32)}" cy="${height - 20 - ((y - minY) / (maxY - minY || 1)) * (height - 60)}" r="3" fill="#58c4dd"/>`).join('');
}

function importanceSVG(features, width, height) {
    const values = Array.isArray(features) ? features : Object.entries(features ?? {}).map(([name, value]) => ({ name, value }));
    if (!values.length) return '<text x="16" y="52" fill="#808080">No feature importance data</text>';
    const max = Math.max(...values.map((item) => Math.abs(Number(item.value) || 0)), 1);
    return values.slice(0, 20).map((item, index) => {
        const value = Number(item.value) || 0;
        const y = 40 + index * 15;
        return `<text x="16" y="${y + 10}" fill="#cccccc" font-size="10">${escapeText(item.name)}</text><rect x="150" y="${y}" width="${Math.abs(value) / max * (width - 170)}" height="10" fill="#f0a45d"/>`;
    }).join('');
}

function histogramSVG(bins, width, height) {
    const values = Array.isArray(bins) ? bins : [];
    if (!values.length) return '<text x="16" y="52" fill="#808080">No histogram data</text>';
    const max = Math.max(...values.map((item) => Number(item.count) || 0), 1);
    const cell = (width - 32) / values.length;
    return values.map((item, index) => `<rect x="${16 + index * cell}" y="${height - 20 - ((Number(item.count) || 0) / max) * (height - 60)}" width="${Math.max(1, cell - 2)}" height="${((Number(item.count) || 0) / max) * (height - 60)}" fill="#58c4dd"/>`).join('');
}

function drawLine(context, values, width, height) {
    if (!values.length) return;
    const min = Math.min(...values); const max = Math.max(...values); const range = max - min || 1;
    context.strokeStyle = '#58c4dd'; context.lineWidth = 2; context.beginPath();
    values.forEach((value, index) => {
        const x = 16 + (index / Math.max(1, values.length - 1)) * (width - 32);
        const y = height - 20 - ((value - min) / range) * (height - 60);
        if (index === 0) context.moveTo(x, y); else context.lineTo(x, y);
    });
    context.stroke();
}

function heatColor(value) {
    const normalized = Math.max(0, Math.min(1, (value + 1) / 2));
    return `rgb(${Math.round(40 + normalized * 190)},${Math.round(80 + (1 - normalized) * 80)},${Math.round(180 - normalized * 120)})`;
}

function escapeText(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[character]));
}
