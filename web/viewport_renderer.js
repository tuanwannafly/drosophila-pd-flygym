const BACKGROUND = '#0b0b0b';
const LINK_COLOR = '#5f6b78';
const NODE_COLOR = '#49a6d8';
const SELECTED_COLOR = '#ffcc66';
const TEXT_COLOR = '#d8dee5';

import { DigitalFly3DRenderer } from './digital_fly_3d_renderer.js';
import { Camera } from './camera.js';

export class ViewportRenderer {
    constructor(workspace, { onSelect = null } = {}) {
        this.workspace = workspace;
        this.container = null;
        this.canvas = null;
        this.context = null;
        this.resizeObserver = null;
        this.resizeHandler = () => this.resize();
        this.devicePixelRatio = 1;
        this.width = 0;
        this.height = 0;
        this.camera = new Camera();
        this.cameraOffsetX = 0;
        this.cameraOffsetY = 0;
        this.zoom = 1;
        this.isPanning = false;
        this.spacePressed = false;
        this.spaceUsedForPan = false;
        this.orbiting = false;
        this.orbitYaw = 0.55;
        this.orbitPitch = -0.35;
        this.digitalFly3D = null;
        this.renderer3D = new DigitalFly3DRenderer();
        this.trajectoryCache = null;
        this.lastPointerX = 0;
        this.lastPointerY = 0;
        this.clickCandidate = false;
        this.onSelect = onSelect;
        this.keyDownHandler = (event) => this.handleKeyDown(event);
        this.keyUpHandler = (event) => this.handleKeyUp(event);
    }

    init(container) {
        this.container = container;
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'viewport-canvas';
        this.canvas.setAttribute('aria-label', 'Scene viewport');
        this.container.replaceChildren(this.canvas);
        this.context = this.canvas.getContext('2d');
        this.canvas.addEventListener('wheel', (event) => this.handleWheel(event), { passive: false });
        this.canvas.addEventListener('pointerdown', (event) => this.handlePointerDown(event));
        this.canvas.addEventListener('pointermove', (event) => this.handlePointerMove(event));
        this.canvas.addEventListener('pointerup', (event) => this.handlePointerUp(event));
        this.canvas.addEventListener('pointercancel', (event) => this.handlePointerUp(event));
        this.canvas.addEventListener('dblclick', () => this.focusSelectedNode());
        this.canvas.addEventListener('contextmenu', (event) => event.preventDefault());
        window.addEventListener('keydown', this.keyDownHandler);
        window.addEventListener('keyup', this.keyUpHandler);

        if (typeof ResizeObserver !== 'undefined') {
            this.resizeObserver = new ResizeObserver(() => this.resize());
            this.resizeObserver.observe(this.container);
        } else {
            window.addEventListener('resize', this.resizeHandler);
        }

        this.resize();
    }

    clear() {
        if (!this.context) return;
        this.context.save();
        this.context.setTransform(1, 0, 0, 1, 0, 0);
        this.context.fillStyle = BACKGROUND;
        this.context.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.context.restore();
    }

    resetView() {
        this.camera.reset();
        this.syncLegacyCamera();
        this.renderer3D.resetCamera();
        this.render();
    }

    setDigitalFly3D(model) {
        this.digitalFly3D = model ?? null;
        this.render();
    }

    setCameraType(type) {
        this.camera.setType(type);
        this.render();
        return this.camera.type;
    }

    setCameraPreset(preset) {
        this.camera.setPreset(preset);
        this.orbitYaw = this.camera.yaw;
        this.orbitPitch = this.camera.pitch;
        this.render();
        return this.camera.preset;
    }

    setOverlay(name, enabled) {
        const value = this.renderer3D.setOverlay(name, enabled);
        this.render();
        return value;
    }

    setBodyPartVisibility(part, visible) {
        const value = this.renderer3D.setBodyPartVisibility(part, visible);
        this.render();
        return value;
    }

    setMeshOpacity(opacity) {
        this.renderer3D.opacity = clamp(Number(opacity) || 0, 0, 1);
        this.render();
        return this.renderer3D.opacity;
    }

    focusBodyPart() {
        this.focusSelectedNode();
    }

    getViewState() {
        this.syncCameraFromLegacy();
        return {
            ...this.camera.toJSON(),
            orbitYaw: this.camera.yaw,
            orbitPitch: this.camera.pitch,
        };
    }

    getCaptureCapabilities() {
        return {
            png: Boolean(this.canvas?.toDataURL),
            svg: true,
            video: Boolean(this.canvas?.captureStream && globalThis.MediaRecorder),
            gif: false,
            note: 'GIF export requires an encoder supplied by the host environment.',
        };
    }

    exportPNG(filename = 'fly-studio-view.png', scale = 1) {
        if (!this.canvas?.toDataURL) return false;
        const factor = clamp(Number(scale) || 1, 1, 4);
        let source = this.canvas;
        if (factor !== 1 && typeof document !== 'undefined') {
            const scaled = document.createElement('canvas');
            scaled.width = Math.floor(this.canvas.width * factor);
            scaled.height = Math.floor(this.canvas.height * factor);
            scaled.getContext('2d')?.drawImage(this.canvas, 0, 0, scaled.width, scaled.height);
            source = scaled;
        }
        const dataUrl = source.toDataURL('image/png');
        downloadDataUrl(dataUrl, filename);
        return true;
    }

    exportSVG(filename = 'fly-studio-view.svg') {
        const png = this.canvas?.toDataURL?.('image/png') ?? '';
        const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${this.width}" height="${this.height}"><image href="${png}" width="100%" height="100%"/></svg>`;
        downloadDataUrl(`data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`, filename);
        return true;
    }

    async recordVideo({ durationMs = 1000, filename = 'fly-studio-view.webm' } = {}) {
        if (!this.canvas?.captureStream || typeof globalThis.MediaRecorder !== 'function') return false;
        const stream = this.canvas.captureStream();
        const mimeType = ['video/webm;codecs=vp9', 'video/webm'].find((type) => globalThis.MediaRecorder.isTypeSupported?.(type));
        const recorder = new globalThis.MediaRecorder(stream, mimeType ? { mimeType } : undefined);
        const chunks = [];
        recorder.ondataavailable = (event) => { if (event.data?.size) chunks.push(event.data); };
        const finished = new Promise((resolve) => {
            recorder.onstop = () => {
                const blob = new Blob(chunks, { type: recorder.mimeType || 'video/webm' });
                downloadBlob(blob, filename);
                stream.getTracks().forEach((track) => track.stop());
                resolve(true);
            };
        });
        recorder.start();
        globalThis.setTimeout(() => recorder.stop(), Math.max(100, Number(durationMs) || 1000));
        return finished;
    }

    destroy() {
        this.resizeObserver?.disconnect();
        this.resizeObserver = null;
        window.removeEventListener('resize', this.resizeHandler);
        window.removeEventListener('keydown', this.keyDownHandler);
        window.removeEventListener('keyup', this.keyUpHandler);
    }

    focusSelectedNode() {
        if (this.digitalFly3D) {
            this.renderer3D.focusSelectedNode(this.digitalFly3D, this.workspace.selectedNode);
            this.cameraOffsetX = 0;
            this.cameraOffsetY = 0;
            this.syncCameraFromLegacy();
            this.render();
            return;
        }
        const selectedNode = this.workspace.selectedNode;
        const nodes = Array.isArray(this.workspace.data?.nodes)
            ? this.workspace.data.nodes
            : [];
        if (!selectedNode || nodes.length === 0) return;

        const layout = layoutNodes(nodes, this.width, this.height);
        const position = layout.positionByNode.get(selectedNode);
        if (!position) return;

        this.cameraOffsetX = -this.zoom * (position.x - this.width / 2);
        this.cameraOffsetY = -this.zoom * (position.y - this.height / 2);
        this.render();
    }

    consumeSpacePan() {
        const usedForPan = this.spaceUsedForPan;
        this.spaceUsedForPan = false;
        return usedForPan;
    }

    resize() {
        if (!this.container || !this.canvas || !this.context) return;

        const width = Math.max(1, Math.floor(this.container.clientWidth));
        const height = Math.max(1, Math.floor(this.container.clientHeight));
        const pixelRatio = Math.max(1, window.devicePixelRatio || 1);
        const changed = width !== this.width
            || height !== this.height
            || pixelRatio !== this.devicePixelRatio;

        if (!changed) return;

        this.width = width;
        this.height = height;
        this.devicePixelRatio = pixelRatio;
        this.canvas.width = Math.floor(width * pixelRatio);
        this.canvas.height = Math.floor(height * pixelRatio);
        this.canvas.style.width = `${width}px`;
        this.canvas.style.height = `${height}px`;
        this.context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
        this.render();
    }

    render() {
        if (!this.context || !this.canvas) return;

        this.clear();

        const nodes = Array.isArray(this.workspace.data?.nodes)
            ? this.workspace.data.nodes
            : [];
        const currentFrame = Number.isInteger(this.workspace.currentFrame)
            ? this.workspace.currentFrame
            : 0;
        const animationFrame = this.workspace.animation?.frames?.[currentFrame] ?? null;
        if (this.digitalFly3D) {
            this.syncCameraFromLegacy();
            this.digitalFly3D.updateFrame(currentFrame);
            this.renderer3D.render(this.context, this.width, this.height, this.digitalFly3D, {
                offsetX: this.camera.offsetX,
                offsetY: this.camera.offsetY,
                zoom: this.camera.zoom,
                orbitYaw: this.camera.yaw,
                orbitPitch: this.camera.pitch,
                cameraType: this.camera.type,
                selectedNode: this.workspace.selectedNode,
                frame: currentFrame,
            });
            return;
        }
        if (nodes.length === 0) {
            this.drawMessage('No Scene Loaded');
            return;
        }

        const layout = layoutNodes(nodes, this.width, this.height);
        applyAnimationFrame(layout, animationFrame, this.width, this.height);
        this.context.save();
        this.applyCameraTransform();
        this.drawGrid();
        this.drawTrajectory();
        this.drawLinks(layout);
        this.drawNodes(layout, this.workspace.selectedNode, currentFrame);
        this.context.restore();
    }

    applyCameraTransform() {
        this.context.translate(
            this.width / 2 + this.cameraOffsetX,
            this.height / 2 + this.cameraOffsetY,
        );
        this.context.scale(this.zoom, this.zoom);
        this.context.translate(-this.width / 2, -this.height / 2);
    }

    focusAnimation() {
        this.resetView();
    }

    handleWheel(event) {
        event.preventDefault();
        const factor = Math.exp(-event.deltaY * 0.001);
        this.zoomAt(factor, event.offsetX, event.offsetY);
    }

    zoomAt(factor, x, y) {
        const nextZoom = clamp(this.zoom * factor, 0.15, 8);
        const centerX = this.width / 2;
        const centerY = this.height / 2;
        const worldX = centerX + (x - centerX - this.cameraOffsetX) / this.zoom;
        const worldY = centerY + (y - centerY - this.cameraOffsetY) / this.zoom;
        this.zoom = nextZoom;
        this.cameraOffsetX = x - centerX - this.zoom * (worldX - centerX);
        this.cameraOffsetY = y - centerY - this.zoom * (worldY - centerY);
        this.syncCameraFromLegacy();
        this.render();
    }

    handlePointerDown(event) {
        const middleButton = event.button === 1;
        const spaceDrag = event.button === 0 && this.spacePressed;
        const orbitDrag = event.button === 2 || (event.button === 1 && event.shiftKey);
        const click = event.button === 0 && !this.spacePressed && !event.shiftKey && Boolean(this.digitalFly3D);
        if (!middleButton && !spaceDrag && !orbitDrag && !click) return;

        if (click) {
            this.clickCandidate = true;
            this.lastPointerX = event.clientX;
            this.lastPointerY = event.clientY;
            return;
        }

        event.preventDefault();
        this.isPanning = true;
        this.orbiting = orbitDrag;
        this.spaceUsedForPan = this.spaceUsedForPan || spaceDrag;
        this.lastPointerX = event.clientX;
        this.lastPointerY = event.clientY;
        this.canvas.setPointerCapture(event.pointerId);
    }

    handlePointerMove(event) {
        if (this.clickCandidate) {
            if (Math.hypot(event.clientX - this.lastPointerX, event.clientY - this.lastPointerY) > 4) this.clickCandidate = false;
            return;
        }
        if (!this.isPanning) return;
        event.preventDefault();
        if (this.orbiting && this.digitalFly3D) {
            this.camera.orbit((event.clientX - this.lastPointerX) * 0.01, (event.clientY - this.lastPointerY) * 0.01);
            this.orbitYaw = this.camera.yaw;
            this.orbitPitch = this.camera.pitch;
            this.lastPointerX = event.clientX;
            this.lastPointerY = event.clientY;
            this.render();
            return;
        }
        this.camera.pan(event.clientX - this.lastPointerX, event.clientY - this.lastPointerY);
        this.syncLegacyCamera();
        this.lastPointerX = event.clientX;
        this.lastPointerY = event.clientY;
        this.render();
    }

    handlePointerUp(event) {
        if (this.clickCandidate) {
            this.clickCandidate = false;
            const rect = this.canvas.getBoundingClientRect();
            const selected = this.renderer3D.hitTest(
                this.width,
                this.height,
                this.digitalFly3D,
                { ...this.getViewState(), selectedNode: this.workspace.selectedNode },
                event.clientX - rect.left,
                event.clientY - rect.top,
            );
            if (selected && this.onSelect) this.onSelect(selected);
            return;
        }
        if (!this.isPanning) return;
        this.isPanning = false;
        this.orbiting = false;
        if (this.canvas.hasPointerCapture(event.pointerId)) {
            this.canvas.releasePointerCapture(event.pointerId);
        }
    }

    handleKeyDown(event) {
        if (event.code === 'Space') this.spacePressed = true;
    }

    handleKeyUp(event) {
        if (event.code === 'Space') this.spacePressed = false;
    }

    syncCameraFromLegacy() {
        this.camera.offsetX = Number(this.cameraOffsetX) || 0;
        this.camera.offsetY = Number(this.cameraOffsetY) || 0;
        this.camera.zoom = clamp(Number(this.zoom) || 1, 0.15, 8);
        this.camera.yaw = Number.isFinite(Number(this.orbitYaw)) ? Number(this.orbitYaw) : this.camera.yaw;
        this.camera.pitch = clamp(Number.isFinite(Number(this.orbitPitch)) ? Number(this.orbitPitch) : this.camera.pitch, -1.55, 1.55);
    }

    syncLegacyCamera() {
        this.cameraOffsetX = this.camera.offsetX;
        this.cameraOffsetY = this.camera.offsetY;
        this.zoom = this.camera.zoom;
        this.orbitYaw = this.camera.yaw;
        this.orbitPitch = this.camera.pitch;
    }

    drawMessage(message) {
        this.context.fillStyle = TEXT_COLOR;
        this.context.font = '16px monospace';
        this.context.textAlign = 'center';
        this.context.textBaseline = 'middle';
        this.context.fillText(message, this.width / 2, this.height / 2);
    }

    drawGrid() {
        const spacing = 40;
        this.context.strokeStyle = '#202b34';
        this.context.lineWidth = 1;
        this.context.beginPath();
        for (let x = 0; x <= this.width; x += spacing) {
            this.context.moveTo(x, 0);
            this.context.lineTo(x, this.height);
        }
        for (let y = 0; y <= this.height; y += spacing) {
            this.context.moveTo(0, y);
            this.context.lineTo(this.width, y);
        }
        this.context.stroke();

        this.context.strokeStyle = '#496070';
        this.context.beginPath();
        this.context.moveTo(this.width / 2, 0);
        this.context.lineTo(this.width / 2, this.height);
        this.context.moveTo(0, this.height / 2);
        this.context.lineTo(this.width, this.height / 2);
        this.context.stroke();
    }

    drawTrajectory() {
        const settings = this.workspace.trajectorySettings;
        if (!settings?.visible) return;
        const points = this.getTrajectoryPoints();
        if (points.length < 2) return;

        const currentFrame = Number.isInteger(this.workspace.currentFrame)
            ? this.workspace.currentFrame
            : 0;
        const visiblePoints = points.filter((point) => point.frame <= currentFrame);
        if (settings.historyTrail && visiblePoints.length >= 2) {
            this.drawTrajectoryLine(visiblePoints, settings.color, settings.thickness);
        }
        if (settings.ghostTrail && visiblePoints.length < points.length) {
            this.drawTrajectoryLine(
                points.filter((point) => point.frame > currentFrame),
                settings.color,
                Math.max(1, settings.thickness / 2),
                true,
            );
        }
    }

    drawTrajectoryLine(points, color, thickness, ghost = false) {
        if (points.length < 2) return;
        this.context.save();
        this.context.strokeStyle = color;
        this.context.globalAlpha = ghost ? 0.3 : 0.85;
        this.context.lineWidth = thickness;
        this.context.beginPath();
        points.forEach((point, index) => {
            if (index === 0) this.context.moveTo(point.x, point.y);
            else this.context.lineTo(point.x, point.y);
        });
        this.context.stroke();
        this.context.restore();
    }

    getTrajectoryPoints() {
        const smoothing = Boolean(this.workspace.trajectorySettings?.smoothing);
        const source = this.workspace.data?.trajectories
            ?? this.workspace.data?.trajectory
            ?? this.workspace.data?.scene?.trajectories
            ?? this.workspace.data?.scene?.trajectory;
        if (this.trajectoryCache?.source === source
            && this.trajectoryCache.width === this.width
            && this.trajectoryCache.height === this.height
            && this.trajectoryCache.smoothing === smoothing) {
            return this.trajectoryCache.points;
        }

        const collection = Array.isArray(source)
            ? source
            : Array.isArray(source?.points)
                ? [source.points]
                : source && typeof source === 'object'
                    ? Object.values(source)
                    : [];
        const rawPoints = collection.flatMap((item) => (
            Array.isArray(item) ? item : item?.points ?? item?.trajectory ?? []
        ));
        const normalizedPoints = rawPoints
            .map((point, index) => normalizeTrajectoryPoint(point, index, this.width, this.height))
            .filter(Boolean)
            .sort((left, right) => left.frame - right.frame);
        const points = smoothing ? smoothTrajectoryPoints(normalizedPoints) : normalizedPoints;
        this.trajectoryCache = { source, points, width: this.width, height: this.height, smoothing };
        return points;
    }

    drawLinks(layout) {
        this.context.strokeStyle = LINK_COLOR;
        this.context.lineWidth = 1.5;
        this.context.beginPath();
        layout.forEach(({ node, parent }) => {
            if (!parent) return;
            const parentPosition = layout.positionByNode.get(parent);
            const position = layout.positionByNode.get(node);
            if (!parentPosition || !position) return;
            this.context.moveTo(parentPosition.x, parentPosition.y);
            this.context.lineTo(position.x, position.y);
        });
        this.context.stroke();
    }

    drawNodes(layout, selectedNode, currentFrame) {
        // The frame is intentionally read-only here; playback will use it later.
        void currentFrame;
        this.context.font = '12px sans-serif';
        this.context.textAlign = 'left';
        this.context.textBaseline = 'middle';

        layout.forEach(({ node, x, y }) => {
            const selected = node === selectedNode;
            this.context.beginPath();
            this.context.arc(x, y, selected ? 8 : 6, 0, Math.PI * 2);
            this.context.fillStyle = selected ? SELECTED_COLOR : NODE_COLOR;
            this.context.fill();
            if (selected) {
                this.context.strokeStyle = '#ffffff';
                this.context.lineWidth = 2;
                this.context.stroke();
            }

            this.context.fillStyle = TEXT_COLOR;
            this.context.fillText(getNodeLabel(node), x + 12, y);
        });
    }
}

function layoutNodes(nodes, width, height) {
    const entries = [];
    let leafCount = 0;
    let maxDepth = 0;

    function collect(node, parent, depth) {
        if (!node || typeof node !== 'object' || Array.isArray(node)) return null;
        maxDepth = Math.max(maxDepth, depth);
        const entry = { node, parent, depth, leafIndex: null, logicalY: 0, x: 0, y: 0 };
        entries.push(entry);
        const children = Array.isArray(node.children) ? node.children : [];
        const childEntries = children
            .map((child) => collect(child, node, depth + 1))
            .filter(Boolean);

        if (childEntries.length === 0) {
            entry.leafIndex = leafCount;
            entry.logicalY = leafCount;
            leafCount += 1;
        } else {
            entry.logicalY = childEntries.reduce((sum, child) => sum + child.logicalY, 0)
                / childEntries.length;
        }
        return entry;
    }

    nodes.forEach((node) => collect(node, null, 0));
    const horizontalPadding = 42;
    const verticalPadding = 32;
    const horizontalStep = maxDepth > 0
        ? (Math.max(horizontalPadding, width - horizontalPadding * 2) / maxDepth)
        : 0;
    const verticalStep = leafCount > 1
        ? (Math.max(verticalPadding, height - verticalPadding * 2) / (leafCount - 1))
        : 0;
    const positionByNode = new Map();

    entries.forEach((entry) => {
        entry.x = horizontalPadding + entry.depth * horizontalStep;
        entry.y = leafCount > 1
            ? verticalPadding + entry.logicalY * verticalStep
            : height / 2;
        positionByNode.set(entry.node, { x: entry.x, y: entry.y });
    });

    return Object.assign(entries, { positionByNode });
}

function getNodeLabel(node) {
    return String(node.name ?? node.id ?? node.type ?? node.kind ?? 'Unnamed node');
}

function applyAnimationFrame(layout, frame, width, height) {
    if (!frame || typeof frame !== 'object') return;
    const frameData = frame.data && typeof frame.data === 'object' ? frame.data : frame;
    const frameNodes = Array.isArray(frameData.nodes) ? frameData.nodes : [];
    const transforms = frameData.nodeTransforms ?? frameData.transforms ?? frameData.positions;

    layout.forEach((entry) => {
        const transform = findFrameTransform(entry.node, frameNodes, transforms, frameData);
        const position = getFramePosition(transform, width, height);
        if (!position) return;
        entry.x = position.x;
        entry.y = position.y;
        layout.positionByNode.set(entry.node, position);
    });
}

function findFrameTransform(node, frameNodes, transforms, frameData) {
    const nodeId = node.id ?? node.name;
    const frameNode = frameNodes.find((candidate) => (
        candidate
        && typeof candidate === 'object'
        && (candidate.id ?? candidate.name) === nodeId
    ));
    if (frameNode) return frameNode;

    if (transforms && typeof transforms === 'object' && nodeId !== undefined) {
        return transforms[nodeId] ?? null;
    }
    if (!frameNodes.length && !transforms && nodeId !== undefined) {
        return frameData[nodeId] ?? null;
    }
    return null;
}

function getFramePosition(transform, width, height) {
    if (!transform || typeof transform !== 'object') return null;
    const position = transform.position ?? transform.translation ?? transform;
    if (Array.isArray(position) && position.length >= 2) {
        return normalizePosition(Number(position[0]), Number(position[1]), width, height);
    }
    if (position && typeof position === 'object') {
        return normalizePosition(Number(position.x), Number(position.y), width, height);
    }
    return null;
}

function normalizePosition(x, y, width, height) {
    if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
    if (x >= 0 && x <= 1 && y >= 0 && y <= 1) {
        return { x: x * width, y: y * height };
    }
    return { x, y };
}

function normalizeTrajectoryPoint(point, index, width, height) {
    if (Array.isArray(point) && point.length >= 2) {
        return normalizeTrajectoryPosition(point[0], point[1], index, width, height);
    }
    if (!point || typeof point !== 'object') return null;
    const position = point.position ?? point.translation ?? point;
    return normalizeTrajectoryPosition(
        position?.x,
        position?.y,
        point.frame ?? point.frameIndex ?? index,
        width,
        height,
    );
}

function normalizeTrajectoryPosition(xValue, yValue, frame, width, height) {
    const x = Number(xValue);
    const y = Number(yValue);
    if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
    return {
        x: x >= 0 && x <= 1 ? x * width : x,
        y: y >= 0 && y <= 1 ? y * height : y,
        frame: Number.isInteger(Number(frame)) ? Number(frame) : 0,
    };
}

function smoothTrajectoryPoints(points) {
    if (points.length < 3) return points;
    return points.map((point, index) => {
        const start = Math.max(0, index - 1);
        const end = Math.min(points.length - 1, index + 1);
        const window = points.slice(start, end + 1);
        return {
            ...point,
            x: window.reduce((sum, item) => sum + item.x, 0) / window.length,
            y: window.reduce((sum, item) => sum + item.y, 0) / window.length,
        };
    });
}

function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
}

function downloadDataUrl(dataUrl, filename) {
    if (typeof document === 'undefined') return;
    const link = document.createElement('a');
    link.href = dataUrl;
    link.download = filename;
    link.click();
}

function downloadBlob(blob, filename) {
    if (typeof URL === 'undefined' || typeof document === 'undefined') return;
    const url = URL.createObjectURL(blob);
    downloadDataUrl(url, filename);
    globalThis.setTimeout(() => URL.revokeObjectURL(url), 0);
}
