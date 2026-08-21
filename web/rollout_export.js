import { chartToSVG } from './rollout_charts.js';

export class RolloutExporter {
    static toJSON(rollout, options = {}) {
        const { workspaceData, ...serializable } = rollout ?? {};
        const value = options.includeRaw === false
            ? { ...serializable, raw: undefined }
            : serializable;
        return JSON.stringify(value, replacer, options.pretty ? 2 : 0);
    }

    static toCSV(rollout, channelName = 'thorax') {
        const channel = rollout?.channels?.[channelName];
        if (channelName === 'joint' && channel && typeof channel === 'object' && !Array.isArray(channel)) {
            const rows = Object.entries(channel).flatMap(([joint, series]) => (
                (Array.isArray(series) ? series : []).map((item, index) => [
                    joint, item.frame ?? index, item.value ?? item.x ?? '',
                ])
            ));
            return [['joint', 'frame', 'value'], ...rows].map((row) => row.map(csvCell).join(',')).join('\n');
        }
        const rows = Array.isArray(channel) ? channel : [];
        const headers = ['frame', 'time_s', 'x', 'y', 'z'];
        const values = rows.map((item, index) => [item.frame ?? index, (item.frame ?? index) * (rollout.timestepS ?? 0), item.x, item.y, item.z]);
        return [headers, ...values].map((row) => row.map(csvCell).join(',')).join('\n');
    }

    static toSVG(type, rollout, options = {}) {
        return chartToSVG(type, rollout, options);
    }

    static download(content, filename, mimeType = 'application/octet-stream') {
        if (typeof document === 'undefined' || typeof URL === 'undefined') {
            throw new Error('Browser download APIs are unavailable.');
        }
        const blob = content instanceof Blob ? content : new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = filename;
        anchor.click();
        setTimeout(() => URL.revokeObjectURL(url), 0);
        return filename;
    }

    static exportPNG(canvas, filename = 'flygym-rollout.png') {
        if (!canvas?.toDataURL) throw new Error('A canvas is required for PNG export.');
        return this.download(dataUrlToBlob(canvas.toDataURL('image/png')), filename, 'image/png');
    }

    static exportSVG(type, rollout, filename = 'flygym-chart.svg', options = {}) {
        return this.download(this.toSVG(type, rollout, options), filename, 'image/svg+xml');
    }

    static async exportVideo(canvas, frames, renderFrame, options = {}) {
        if (!canvas?.captureStream || typeof MediaRecorder === 'undefined') {
            throw new Error('Video export requires Canvas captureStream and MediaRecorder.');
        }
        if (typeof renderFrame !== 'function') throw new Error('renderFrame callback is required.');
        const fps = Number(options.fps ?? 30);
        const stream = canvas.captureStream(fps);
        const chunks = [];
        const recorder = new MediaRecorder(stream, { mimeType: options.mimeType ?? 'video/webm' });
        recorder.ondataavailable = (event) => { if (event.data.size) chunks.push(event.data); };
        const completed = new Promise((resolve, reject) => {
            recorder.onerror = () => reject(recorder.error ?? new Error('Video recording failed.'));
            recorder.onstop = () => resolve(new Blob(chunks, { type: recorder.mimeType }));
        });
        recorder.start();
        for (const frame of frames ?? []) {
            renderFrame(frame);
            await nextAnimationFrame();
        }
        recorder.stop();
        return completed;
    }

    static exportAnimation(...args) {
        return this.exportVideo(...args);
    }
}

function csvCell(value) {
    const text = value === null || value === undefined ? '' : String(value);
    return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function dataUrlToBlob(dataUrl) {
    const [header, encoded] = dataUrl.split(',');
    const binary = atob(encoded);
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    return new Blob([bytes], { type: header.match(/data:(.*?);/)?.[1] ?? 'image/png' });
}

function replacer(key, value) {
    return key === 'raw' && value === undefined ? undefined : value;
}

function nextAnimationFrame() {
    return new Promise((resolve) => {
        if (typeof requestAnimationFrame === 'function') requestAnimationFrame(resolve);
        else setTimeout(resolve, 1000 / 30);
    });
}
