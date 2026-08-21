import { renderAnalyticsSVG } from './parkinson_visualization.js';

export class AnalyticsExporter {
    static toJSON(value, pretty = true) {
        return JSON.stringify(value, null, pretty ? 2 : 0);
    }

    static toCSV(rows = []) {
        if (!rows.length) return '';
        const columns = [...new Set(rows.flatMap((row) => Object.keys(row)))];
        return [columns, ...rows.map((row) => columns.map((column) => row[column] ?? ''))].map((row) => row.map(csvCell).join(',')).join('\n');
    }

    static toMarkdown(title, value) {
        return `# ${title}\n\nScope: computational analytics only; no biological validation is implied.\n\n\`\`\`json\n${this.toJSON(value)}\n\`\`\`\n`;
    }

    static toHTML(title, value) {
        return `<article><h1>${escapeText(title)}</h1><p>Computational analytics only; no biological validation is implied.</p><pre>${escapeText(this.toJSON(value))}</pre></article>`;
    }

    static toSVG(type, payload, options = {}) {
        return renderAnalyticsSVG(type, payload, options);
    }

    static download(content, filename, type = 'application/octet-stream') {
        if (typeof document === 'undefined') throw new Error('Browser download APIs are unavailable.');
        const url = URL.createObjectURL(new Blob([content], { type }));
        const link = document.createElement('a'); link.href = url; link.download = filename; link.click();
        setTimeout(() => URL.revokeObjectURL(url), 0);
        return filename;
    }

    static exportPNG(canvas, filename = 'analytics.png') {
        if (!canvas?.toDataURL) throw new Error('A canvas is required for PNG export.');
        return this.download(dataURLToBlob(canvas.toDataURL('image/png')), filename, 'image/png');
    }
}

function csvCell(value) {
    const text = value === null || value === undefined ? '' : String(value);
    return /[,"\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function dataURLToBlob(dataURL) {
    const [header, encoded] = dataURL.split(',');
    const binary = atob(encoded);
    return new Blob([Uint8Array.from(binary, (character) => character.charCodeAt(0))], { type: header.match(/data:(.*?);/)?.[1] ?? 'image/png' });
}

function escapeText(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
}
