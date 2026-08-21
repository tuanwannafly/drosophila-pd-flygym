export const CAMERA_TYPES = Object.freeze(['perspective', 'orthographic']);

export const CAMERA_PRESETS = Object.freeze({
    Front: Object.freeze({ yaw: 0, pitch: -0.25 }),
    Back: Object.freeze({ yaw: Math.PI, pitch: -0.25 }),
    Left: Object.freeze({ yaw: -Math.PI / 2, pitch: -0.25 }),
    Right: Object.freeze({ yaw: Math.PI / 2, pitch: -0.25 }),
    Top: Object.freeze({ yaw: 0, pitch: -Math.PI / 2 + 0.08 }),
    Bottom: Object.freeze({ yaw: 0, pitch: Math.PI / 2 - 0.08 }),
    Isometric: Object.freeze({ yaw: Math.PI / 4, pitch: -Math.PI / 6 }),
});

export class Camera {
    constructor({ type = 'perspective', zoom = 1, offsetX = 0, offsetY = 0 } = {}) {
        this.type = CAMERA_TYPES.includes(type) ? type : 'perspective';
        this.zoom = clamp(Number(zoom) || 1, 0.15, 8);
        this.offsetX = Number(offsetX) || 0;
        this.offsetY = Number(offsetY) || 0;
        this.yaw = 0.55;
        this.pitch = -0.35;
        this.preset = 'Isometric';
    }

    setType(type) {
        if (CAMERA_TYPES.includes(type)) this.type = type;
        return this.type;
    }

    setPreset(preset) {
        const next = CAMERA_PRESETS[preset];
        if (!next) return this.preset;
        this.preset = preset;
        this.yaw = next.yaw;
        this.pitch = next.pitch;
        return this.preset;
    }

    reset() {
        this.zoom = 1;
        this.offsetX = 0;
        this.offsetY = 0;
        this.setPreset('Isometric');
        return this;
    }

    orbit(deltaYaw, deltaPitch) {
        this.yaw += Number(deltaYaw) || 0;
        this.pitch = clamp(this.pitch + (Number(deltaPitch) || 0), -Math.PI / 2 + 0.02, Math.PI / 2 - 0.02);
        this.preset = 'Free';
        return this;
    }

    pan(deltaX, deltaY) {
        this.offsetX += Number(deltaX) || 0;
        this.offsetY += Number(deltaY) || 0;
        return this;
    }

    zoomBy(factor) {
        this.zoom = clamp(this.zoom * (Number(factor) || 1), 0.15, 8);
        return this.zoom;
    }

    toJSON() {
        return {
            type: this.type,
            zoom: this.zoom,
            offsetX: this.offsetX,
            offsetY: this.offsetY,
            yaw: this.yaw,
            pitch: this.pitch,
            preset: this.preset,
        };
    }

    restore(value = {}) {
        this.setType(value.type);
        this.zoom = clamp(Number(value.zoom) || 1, 0.15, 8);
        this.offsetX = Number(value.offsetX) || 0;
        this.offsetY = Number(value.offsetY) || 0;
        this.yaw = Number.isFinite(Number(value.yaw)) ? Number(value.yaw) : this.yaw;
        this.pitch = clamp(Number.isFinite(Number(value.pitch)) ? Number(value.pitch) : this.pitch, -Math.PI / 2 + 0.02, Math.PI / 2 - 0.02);
        this.preset = value.preset ?? 'Free';
        return this;
    }
}

function clamp(value, minimum, maximum) {
    return Math.min(maximum, Math.max(minimum, value));
}
