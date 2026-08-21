import * as THREE from 'three';
import { CameraController } from './camera_controller.js';
import { DigitalFlyMesh } from './digital_fly_mesh.js';
import { DigitalFlyScene } from './digital_fly_scene.js';
import { JointAnimator } from './joint_animator.js';
import { SkeletonRenderer } from './skeleton_renderer.js';
import { TimelineController } from './timeline_controller.js';
import { TrajectoryRenderer } from './trajectory_renderer.js';
import { loadPoseJSON } from './pose_loader.js';

/** Three.js viewer composition root. It consumes imported pose data only. */
export class Viewer {
    constructor({ onFrameChange = null } = {}) {
        this.onFrameChange = onFrameChange;
        this.container = null;
        this.shell = null;
        this.viewport = null;
        this.timelineRoot = null;
        this.renderer = null;
        this.sceneModel = null;
        this.cameraController = null;
        this.mesh = null;
        this.skeleton = null;
        this.trajectory = null;
        this.animator = new JointAnimator();
        this.timeline = null;
        this.poseDocument = null;
        this.digitalFly3D = null;
        this.frameCount = 0;
        this.fps = 60;
        this.currentFrame = 0;
        this.speed = 1;
        this.loop = false;
        this.shadows = true;
        this.playing = false;
        this.animationFrameId = null;
        this.lastTimestamp = null;
        this.frameAccumulator = 0;
        this.resizeObserver = null;
        this.resizeHandler = () => this.resize();
    }

    init(container) {
        this.container = container;
        this.shell = document.createElement('section');
        this.shell.className = 'three-viewer-shell hidden';
        this.shell.setAttribute('aria-label', 'Three.js Digital Fly viewer');
        this.viewport = document.createElement('div');
        this.viewport.className = 'three-viewer-viewport';
        this.timelineRoot = document.createElement('div');
        this.shell.append(this.viewport, this.timelineRoot);
        container.append(this.shell);

        try {
            this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
            this.renderer.setPixelRatio(Math.min(2, globalThis.devicePixelRatio || 1));
            this.renderer.setClearColor(0x0b0f14, 1);
            this.renderer.outputColorSpace = THREE.SRGBColorSpace;
            this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
            this.renderer.toneMappingExposure = 1.05;
            this.renderer.shadowMap.enabled = true;
            this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            this.renderer.domElement.className = 'three-viewer-canvas';
            this.renderer.domElement.setAttribute('aria-label', '3D Digital Fly viewport');
            this.viewport.append(this.renderer.domElement);
            this.sceneModel = new DigitalFlyScene();
            this.mesh = new DigitalFlyMesh();
            this.skeleton = new SkeletonRenderer();
            this.trajectory = new TrajectoryRenderer();
            this.sceneModel.root.add(this.mesh.group, this.skeleton.group, this.trajectory.group);
            this.cameraController = new CameraController({
                renderer: this.renderer,
                scene: this.sceneModel.scene,
                domElement: this.renderer.domElement,
                onChange: () => this.render(),
            });
            this.timeline = new TimelineController({
                onFrame: (frame) => this.setFrame(frame, { notify: true }),
                onPlay: () => this.play(),
                onPause: () => this.pause(),
                onStop: () => this.stop(),
                onSpeed: (speed) => { this.speed = speed; },
                onLoop: (enabled) => { this.loop = enabled; },
                onReset: () => this.resetView(),
                onCameraPreset: (preset) => this.setCameraPreset(preset),
                onAxes: (enabled) => { this.sceneModel.setAxesVisible(enabled); this.render(); },
                onGrid: (enabled) => { this.sceneModel.setGridVisible(enabled); this.render(); },
                onFloor: (enabled) => { this.sceneModel.setGroundVisible(enabled); this.render(); },
                onShadow: (enabled) => this.setShadows(enabled),
            });
            this.timeline.init(this.timelineRoot);
            this.resizeObserver = typeof ResizeObserver === 'function'
                ? new ResizeObserver(() => this.resize())
                : null;
            this.resizeObserver?.observe(this.viewport);
            if (!this.resizeObserver) window.addEventListener('resize', this.resizeHandler);
            this.resize();
        } catch (error) {
            this.showError(`3D viewer unavailable: ${error.message}`);
            console.error('Unable to initialize Three.js viewer:', error);
        }
        return this;
    }

    async loadPose(input) {
        const documentData = await loadPoseJSON(input);
        this.poseDocument = documentData;
        this.digitalFly3D = null;
        this.animator.setFrames(documentData.frames);
        this.fps = documentData.fps;
        this.frameCount = documentData.frame_count;
        await this.mesh.loadMetadata(documentData.mesh);
        this.trajectory.updateFromPose(documentData);
        this.timeline.setRange(this.frameCount);
        this.show();
        this.fitPoseToCamera(documentData);
        this.setFrame(0);
        return documentData;
    }

    setDigitalFly3D(model) {
        this.digitalFly3D = model ?? null;
        this.poseDocument = null;
        this.animator.setFrames([]);
        this.frameCount = inferFrameCount(model);
        this.fps = Number(model?.fly?.metadata?.fps ?? 60) || 60;
        this.mesh.useFallback();
        this.trajectory.updateFromDigitalFly3D(model);
        this.timeline?.setRange(this.frameCount);
        if (model) {
            this.show();
            this.fitDigitalFlyToCamera(model);
            this.setFrame(0);
        } else {
            this.clear();
        }
    }

    clear() {
        this.pause();
        this.poseDocument = null;
        this.digitalFly3D = null;
        this.frameCount = 0;
        this.currentFrame = 0;
        this.animator.setFrames([]);
        this.trajectory?.clear();
        this.skeleton?.clear();
        this.timeline?.setRange(0);
        this.hide();
        this.render();
    }

    setFrame(frame, { notify = false } = {}) {
        const maximum = Math.max(0, this.frameCount - 1);
        this.currentFrame = Math.min(maximum, Math.max(0, Math.round(Number(frame) || 0)));
        this.timeline?.setFrame(this.currentFrame, this.frameCount, {
            fps: this.fps,
            speed: this.speed,
            time: this.currentTime(),
        });
        this.render();
        if (notify) this.onFrameChange?.(this.currentFrame);
        return this.currentFrame;
    }

    play() {
        if (this.playing || this.frameCount <= 1) return;
        this.playing = true;
        this.lastTimestamp = null;
        this.frameAccumulator = 0;
        this.timeline?.setPlaying(true);
        this.schedule();
    }

    pause() {
        this.playing = false;
        if (this.animationFrameId !== null) cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
        this.lastTimestamp = null;
        this.timeline?.setPlaying(false);
    }

    stop() {
        this.pause();
        this.setFrame(0, { notify: true });
    }

    schedule() {
        if (!this.playing) return;
        this.animationFrameId = requestAnimationFrame((timestamp) => this.tick(timestamp));
    }

    tick(timestamp) {
        if (!this.playing) return;
        if (this.lastTimestamp === null) this.lastTimestamp = timestamp;
        const elapsed = Math.min(0.1, Math.max(0, (timestamp - this.lastTimestamp) / 1000));
        this.lastTimestamp = timestamp;
        this.frameAccumulator += elapsed * this.fps * this.speed;
        const steps = Math.floor(this.frameAccumulator);
        if (steps > 0) {
            this.frameAccumulator -= steps;
            let next = this.currentFrame + steps;
            if (next >= this.frameCount) {
                if (this.loop) next %= this.frameCount;
                else { next = this.frameCount - 1; this.pause(); }
            }
            this.setFrame(next, { notify: true });
        }
        this.schedule();
    }

    setSpeed(speed) {
        this.speed = Math.max(0.05, Number(speed) || 1);
        this.timeline?.setFrame(this.currentFrame, this.frameCount, {
            fps: this.fps,
            speed: this.speed,
            time: this.currentTime(),
        });
        return this.speed;
    }
    setLoop(loop) { this.loop = Boolean(loop); return this.loop; }
    setCameraPreset(preset) { return this.cameraController?.setPreset(String(preset).toLowerCase()); }
    setCameraType(type) { return this.cameraController?.setType(type); }
    resetView() {
        if (this.poseDocument) this.fitPoseToCamera(this.poseDocument);
        else if (this.digitalFly3D) this.fitDigitalFlyToCamera(this.digitalFly3D);
        else this.cameraController?.reset();
        this.render();
    }
    focusBodyPart() { this.focus(); }

    focus(target = null) {
        const frame = this.poseDocument?.frames?.[this.currentFrame];
        const position = target ?? frame?.thorax ?? this.digitalFly3D?.lastFrameState?.bones?.find((bone) => bone.id === 'thorax')?.worldTransform?.translation;
        if (Array.isArray(position)) this.cameraController?.focus(new THREE.Vector3(...position));
        this.render();
    }

    setVisible(name, visible) {
        const target = { mesh: this.mesh?.group, skeleton: this.skeleton?.group, trajectory: this.trajectory?.group }[name];
        if (target) target.visible = Boolean(visible);
    }

    setShadows(enabled) {
        this.shadows = Boolean(enabled);
        if (this.renderer) this.renderer.shadowMap.enabled = this.shadows;
        this.sceneModel?.setShadowEnabled(this.shadows);
        this.mesh?.setShadows(this.shadows);
        this.render();
    }

    currentTime() {
        const frame = this.poseDocument?.frames?.[this.currentFrame];
        if (Number.isFinite(frame?.time)) return Number(frame.time);
        return this.fps > 0 ? this.currentFrame / this.fps : 0;
    }

    fitPoseToCamera(poseDocument) {
        const points = [];
        for (const frame of poseDocument?.frames ?? []) {
            if (Array.isArray(frame?.thorax)) points.push(frame.thorax);
            if (Array.isArray(frame?.COM)) points.push(frame.COM);
        }
        this.cameraController?.fitToPoints(points, { preset: 'demo' });
    }

    fitDigitalFlyToCamera(model) {
        const points = [];
        const records = model?.fly?.trajectories?.list?.() ?? [];
        records.forEach((record) => points.push(...flattenPoints(record.data)));
        this.cameraController?.fitToPoints(points, { preset: 'demo' });
    }

    resize() {
        if (!this.renderer || !this.viewport) return;
        const width = Math.max(1, this.viewport.clientWidth);
        const height = Math.max(1, this.viewport.clientHeight);
        this.renderer.setSize(width, height, false);
        this.cameraController?.resize();
        this.render();
    }

    render() {
        if (!this.renderer || !this.sceneModel) return;
        let snapshot = null;
        if (this.poseDocument) {
            const frame = this.animator.sample(this.currentFrame);
            this.mesh.updateFromFrame(frame);
            this.skeleton.updateFromPoseFrame(frame);
        } else if (this.digitalFly3D) {
            snapshot = this.digitalFly3D.updateFrame(this.currentFrame);
            this.mesh.updateFromSnapshot(snapshot);
            this.skeleton.updateFromSnapshot(snapshot);
        }
        this.renderer.render(this.sceneModel.scene, this.cameraController.getCamera());
        return snapshot;
    }

    show() { this.shell?.classList.remove('hidden'); }
    hide() { this.shell?.classList.add('hidden'); }

    showError(message) {
        if (!this.shell) return;
        this.shell.classList.remove('hidden');
        this.shell.replaceChildren();
        const notice = document.createElement('p');
        notice.className = 'three-viewer-error';
        notice.textContent = message;
        this.shell.append(notice);
    }

    destroy() {
        this.pause();
        this.resizeObserver?.disconnect();
        if (!this.resizeObserver) window.removeEventListener('resize', this.resizeHandler);
        this.cameraController?.dispose();
        this.timeline?.destroy();
        this.mesh?.dispose();
        this.skeleton?.dispose();
        this.trajectory?.dispose();
        this.sceneModel?.dispose();
        this.renderer?.dispose();
        this.shell?.remove();
    }
}

function inferFrameCount(model) {
    const records = model?.fly?.trajectories?.list?.() ?? [];
    const lengths = records.map((record) => seriesLength(record.data));
    return Math.max(0, ...lengths);
}

function seriesLength(value) {
    if (Array.isArray(value)) return value.length;
    if (value && typeof value === 'object') {
        if (Array.isArray(value.frames)) return value.frames.length;
        if (Array.isArray(value.values)) return value.values.length;
        if (Array.isArray(value.points)) return value.points.length;
    }
    return 0;
}

function flattenPoints(value) {
    if (Array.isArray(value)) {
        if (value.length >= 3 && value.slice(0, 3).every((item) => Number.isFinite(Number(item)))) {
            return [value.slice(0, 3).map(Number)];
        }
        return value.flatMap((item) => flattenPoints(item));
    }
    if (value && typeof value === 'object') {
        return Object.values(value).flatMap((item) => flattenPoints(item));
    }
    return [];
}
