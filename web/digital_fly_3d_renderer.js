const BACKGROUND = '#0b0b0b';
const GRID = '#26313a';
const AXIS_X = '#d26a6a';
const AXIS_Y = '#78c091';
const AXIS_Z = '#6f9ee8';
const BONE = '#58c4dd';
const JOINT = '#f0b429';
const SELECTED = '#ffcc66';
const TEXT = '#d8dee5';

export class DigitalFly3DRenderer {
    constructor() {
        this.target = [0, 0, 0];
        this.distance = 6;
        this.showGround = true;
        this.showAxes = true;
        this.showJointAxes = true;
        this.showCOM = true;
        this.showTrajectory = true;
        this.showSkeleton = true;
        this.showBodySegments = true;
        this.showVelocity = false;
        this.showAcceleration = false;
        this.showAngularVelocity = false;
        this.showAngularAcceleration = false;
        this.showLabels = false;
        this.showContacts = true;
        this.showHeatmap = false;
        this.bodyPartVisibility = {
            head: true, thorax: true, abdomen: true, legs: true,
            wings: true, eyes: true, antenna: true,
        };
        this.bodyPartColors = {
            head: '#d6a06d', thorax: '#d8915f', abdomen: '#b86d4c',
            legs: '#58c4dd', wings: '#b6d7e5', eyes: '#f7f7f7', antenna: '#f0b429',
        };
        this.opacity = 0.78;
    }

    resetCamera() {
        this.target = [0, 0, 0];
        this.distance = 6;
    }

    focusSelectedNode(model, selectedNode) {
        const id = selectedNode?.id?.replace(/^flygym-/, '') ?? selectedNode?.name;
        const bone = model?.skeleton.bones.get(id) ?? model?.skeleton.bonesInOrder().find((item) => item.name === selectedNode?.name);
        if (bone) this.target = [...bone.worldTransform.translation];
    }

    render(context, width, height, model, camera = {}) {
        if (!context || !model) return;
        context.save();
        context.fillStyle = BACKGROUND;
        context.fillRect(0, 0, width, height);
        const projection = (point) => projectPoint(point, width, height, camera, this.target, this.distance);
        if (this.showGround) this.drawGround(context, width, height, projection);
        if (this.showAxes) this.drawAxes(context, width, height, projection);
        if (this.showTrajectory) this.drawTrajectory(context, width, height, projection, model);
        if (this.showBodySegments) this.drawBodyMesh(context, projection, model, camera.selectedNode);
        if (this.showSkeleton) this.drawSkeleton(context, projection, model, camera.selectedNode);
        if (this.showCOM) this.drawCOM(context, projection, model);
        if (this.showVelocity || this.showAcceleration || this.showAngularVelocity || this.showAngularAcceleration) this.drawMotionVectors(context, projection, model, camera.frame);
        if (this.showContacts) this.drawContacts(context, projection, model, camera.frame);
        if (this.showHeatmap) this.drawHeatmap(context, projection, model, camera.frame);
        if (this.showLabels) this.drawBodyLabels(context, projection, model, camera.selectedNode);
        this.drawLabel(context, width, model, camera.frame);
        context.restore();
    }

    setOverlay(name, enabled) {
        const aliases = { trajectory: 'showTrajectory', skeleton: 'showSkeleton', mesh: 'showBodySegments', axes: 'showAxes', com: 'showCOM', jointAxes: 'showJointAxes', velocity: 'showVelocity', acceleration: 'showAcceleration', angular: 'showAngularVelocity', angularVelocity: 'showAngularVelocity', angularAcceleration: 'showAngularAcceleration', 'angular-acceleration': 'showAngularAcceleration', labels: 'showLabels', contacts: 'showContacts', heatmap: 'showHeatmap' };
        const key = aliases[name] ?? name;
        if (key in this) this[key] = Boolean(enabled);
        return this[key];
    }

    setBodyPartVisibility(part, visible) {
        if (part in this.bodyPartVisibility) this.bodyPartVisibility[part] = Boolean(visible);
        return this.bodyPartVisibility[part];
    }

    setBodyPartColor(part, color) {
        if (part in this.bodyPartColors && typeof color === 'string') this.bodyPartColors[part] = color;
        return this.bodyPartColors[part];
    }

    drawBodyMesh(context, projection, model, selectedNode) {
        const bones = model.skeleton;
        const selectedId = selectedNode?.id?.replace(/^flygym-/, '') ?? selectedNode?.name;
        const drawPart = (part, boneId, radius, shape = 'ellipse') => {
            if (!this.bodyPartVisibility[part]) return;
            const bone = bones.bones.get(boneId);
            const point = bone && projection(bone.worldTransform.translation);
            if (!point) return;
            const selected = boneId === selectedId;
            context.save();
            context.globalAlpha = selected ? 1 : this.opacity;
            context.fillStyle = this.bodyPartColors[part];
            context.strokeStyle = selected ? SELECTED : this.bodyPartColors[part];
            context.lineWidth = selected ? 2.5 : 1;
            if (shape === 'wing') {
                const side = boneId.endsWith('_L') ? -1 : 1;
                context.beginPath();
                context.moveTo(point.x, point.y);
                context.lineTo(point.x + side * radius * 2.2, point.y - radius * 0.75);
                context.lineTo(point.x + side * radius * 2.8, point.y + radius * 0.35);
                context.closePath();
                context.fill();
                context.stroke();
            } else {
                context.beginPath();
                context.ellipse(point.x, point.y, radius * (shape === 'head' ? 0.85 : 1.2), radius, 0, 0, Math.PI * 2);
                context.fill();
                context.stroke();
            }
            context.restore();
        };
        drawPart('thorax', 'thorax', 15);
        drawPart('abdomen', 'abdomen', 12);
        drawPart('head', 'head', 11, 'head');
        drawPart('wings', 'wing_L', 14, 'wing');
        drawPart('wings', 'wing_R', 14, 'wing');
        if (this.bodyPartVisibility.eyes) {
            ['left', 'right'].forEach((side, index) => this.drawSmallMarker(context, projection, bones.bones.get('head'), side, index));
        }
        if (this.bodyPartVisibility.antenna) this.drawAntenna(context, projection, bones.bones.get('head'));
        if (this.bodyPartVisibility.legs) {
            ['leg_FL', 'leg_ML', 'leg_HL', 'leg_FR', 'leg_MR', 'leg_HR'].forEach((id) => {
                const bone = bones.bones.get(id);
                const parent = bone && bones.bones.get(bone.parentId);
                if (bone && parent) drawProjectedLine(context, projection, [parent.worldTransform.translation, bone.worldTransform.translation], this.bodyPartColors.legs, 4);
            });
        }
    }

    drawSmallMarker(context, projection, bone, side, index) {
        if (!bone) return;
        const position = bone.worldTransform.translation.map((value, axis) => value + (axis === 0 ? (index ? 0.08 : -0.08) : axis === 2 ? 0.08 : 0));
        const point = projection(position);
        if (!point) return;
        context.beginPath();
        context.arc(point.x, point.y, 3, 0, Math.PI * 2);
        context.fillStyle = this.bodyPartColors.eyes;
        context.fill();
        void side;
    }

    drawAntenna(context, projection, bone) {
        if (!bone) return;
        const start = bone.worldTransform.translation;
        [[-0.18, 0.15, 0.12], [0.18, 0.15, 0.12]].forEach((offset) => {
            drawProjectedLine(context, projection, [start, add(start, offset)], this.bodyPartColors.antenna, 1.5);
        });
    }

    drawGround(context, width, height, projection) {
        context.save();
        context.strokeStyle = GRID;
        context.lineWidth = 1;
        for (let value = -4; value <= 4; value += 0.5) {
            drawProjectedLine(context, projection, [[value, -1.1, -4], [value, -1.1, 4]]);
            drawProjectedLine(context, projection, [[-4, -1.1, value], [4, -1.1, value]]);
        }
        context.restore();
    }

    drawAxes(context, width, height, projection) {
        const origin = [0, -1.1, 0];
        drawProjectedLine(context, projection, [origin, [1.2, -1.1, 0]], AXIS_X, 2);
        drawProjectedLine(context, projection, [origin, [0, 0.1, 0]], AXIS_Y, 2);
        drawProjectedLine(context, projection, [origin, [0, -1.1, 1.2]], AXIS_Z, 2);
    }

    drawTrajectory(context, width, height, projection, model) {
        const records = model.fly.trajectories.list().filter((record) => ['thorax', 'com'].includes(record.metadata?.channel));
        records.forEach((record) => {
            const points = Array.from({ length: seriesLength(record.data) }, (_, frame) => sampleVector(record.data, frame)).filter(Boolean);
            if (points.length < 2) return;
            context.save();
            context.strokeStyle = '#708090';
            context.globalAlpha = 0.65;
            context.lineWidth = 1.5;
            context.beginPath();
            points.forEach((point, index) => {
                const screen = projection(point);
                if (!screen) return;
                if (index === 0) context.moveTo(screen.x, screen.y);
                else context.lineTo(screen.x, screen.y);
            });
            context.stroke();
            context.restore();
        });
    }

    drawMotionVectors(context, projection, model, frame) {
        const record = model.fly.trajectories.list().find((item) => item.metadata?.channel === 'thorax' || item.metadata?.channel === 'com');
        if (!record || frame < 1) return;
        const current = sampleVector(record.data, frame);
        const previous = sampleVector(record.data, frame - 1);
        if (!current || !previous) return;
        const velocity = scale(subtract(current, previous), 4);
        if (this.showVelocity) drawArrow(context, projection, current, add(current, scale(velocity, 0.35)), '#f0b429', 2);
        if (this.showAcceleration && frame > 1) {
            const before = sampleVector(record.data, frame - 2);
            if (before) drawArrow(context, projection, current, add(current, scale(subtract(velocity, subtract(previous, before)), 0.2)), '#78c091', 2);
        }
        if (this.showAngularVelocity) {
            const root = model.skeleton.bones.get('fly');
            if (root) drawArrow(context, projection, root.worldTransform.translation, add(root.worldTransform.translation, [0, 0.35, 0]), '#d26a6a', 2);
        }
    }

    drawHeatmap(context, projection, model, frame) {
        const record = model.fly.trajectories.list().find((item) => ['heatmap', 'joint_error'].includes(item.metadata?.channel));
        if (!record) return;
        const value = sampleScalar(record.data, frame);
        const thorax = model.skeleton.bones.get('thorax');
        const point = thorax && projection(thorax.worldTransform.translation);
        if (!point || !Number.isFinite(value)) return;
        context.save();
        context.globalAlpha = 0.35;
        context.fillStyle = `hsl(${Math.max(0, 120 - Math.min(120, Math.abs(value) * 120))} 80% 55%)`;
        context.beginPath();
        context.arc(point.x, point.y, 24, 0, Math.PI * 2);
        context.fill();
        context.restore();
    }

    drawContacts(context, projection, model, frame) {
        const records = model.fly.trajectories.list().filter((item) => item.metadata?.channel === 'contact' || item.metadata?.channel === 'ground_contact');
        records.forEach((record) => {
            const value = sampleScalar(record.data, frame);
            if (!Number.isFinite(value) || value <= 0) return;
            const bone = model.skeleton.bonesInOrder().find((item) => item.name.toLowerCase().includes(String(record.metadata?.name ?? '').toLowerCase()));
            const point = bone && projection(bone.worldTransform.translation);
            if (!point) return;
            context.beginPath();
            context.arc(point.x, point.y, 5, 0, Math.PI * 2);
            context.strokeStyle = '#78c091';
            context.lineWidth = 2;
            context.stroke();
        });
    }

    drawBodyLabels(context, projection, model, selectedNode) {
        const selectedId = selectedNode?.id?.replace(/^flygym-/, '') ?? selectedNode?.name;
        model.skeleton.bonesInOrder().forEach((bone) => {
            const point = projection(bone.worldTransform.translation);
            if (!point) return;
            context.fillStyle = bone.id === selectedId ? SELECTED : TEXT;
            context.font = '11px sans-serif';
            context.fillText(bone.name, point.x + 7, point.y - 7);
        });
    }

    hitTest(width, height, model, camera, x, y, radius = 14) {
        if (!model?.skeleton) return null;
        const projection = (point) => projectPoint(point, width, height, camera, this.target, this.distance);
        let best = null;
        model.skeleton.bonesInOrder().forEach((bone) => {
            const point = projection(bone.worldTransform.translation);
            if (!point) return;
            const distance = Math.hypot(point.x - x, point.y - y);
            if (distance <= radius && (!best || distance < best.distance)) {
                best = { distance, node: { id: `flygym-${bone.id}`, name: bone.name, type: 'flygym-body-part', metadata: { source: 'imported rollout', component: bone.id } } };
            }
        });
        return best?.node ?? null;
    }

    drawSkeleton(context, projection, model, selectedNode) {
        const selectedId = selectedNode?.id?.replace(/^flygym-/, '') ?? selectedNode?.name;
        model.skeleton.bonesInOrder().forEach((bone) => {
            const start = projection(bone.worldTransform.translation);
            if (!start) return;
            bone.children.forEach((childId) => {
                const child = model.skeleton.bones.get(childId);
                const end = projection(child.worldTransform.translation);
                if (end) drawProjectedLine(context, projection, [bone.worldTransform.translation, child.worldTransform.translation], BONE, 2);
            });
            context.beginPath();
            context.arc(start.x, start.y, bone.id === selectedId ? 6 : 4, 0, Math.PI * 2);
            context.fillStyle = bone.id === selectedId ? SELECTED : JOINT;
            context.fill();
            if (this.showJointAxes) this.drawJointAxis(context, projection, bone);
        });
    }

    drawJointAxis(context, projection, bone) {
        const start = bone.worldTransform.translation;
        const direction = rotateVector(bone.worldTransform.quaternion, bone.joint.axis);
        drawProjectedLine(context, projection, [start, add(start, scale(direction, 0.18))], AXIS_Z, 1);
    }

    drawCOM(context, projection, model) {
        const position = model.lastFrameState?.com ?? model.skeleton.getBone('thorax').worldTransform.translation;
        const point = projection(position);
        if (!point) return;
        context.beginPath();
        context.arc(point.x, point.y, 5, 0, Math.PI * 2);
        context.strokeStyle = '#ffffff';
        context.lineWidth = 2;
        context.stroke();
    }

    drawLabel(context, width, model, frame) {
        context.fillStyle = TEXT;
        context.font = '12px sans-serif';
        context.textAlign = 'left';
        context.fillText(`Digital Fly 3D  |  frame ${frame ?? 0}`, 12, 18);
        context.textAlign = 'right';
        context.fillText(`${model.skeleton.bones.size} bones`, width - 12, 18);
    }
}

function projectPoint(point, width, height, camera, target, distance) {
    if (!Array.isArray(point) || point.length < 3 || point.some((value) => !Number.isFinite(Number(value)))) return null;
    const yaw = Number(camera.orbitYaw ?? 0.55);
    const pitch = Number(camera.orbitPitch ?? -0.35);
    const dx = Number(point[0]) - target[0];
    const dy = Number(point[1]) - target[1];
    const dz = Number(point[2]) - target[2];
    const cosYaw = Math.cos(yaw);
    const sinYaw = Math.sin(yaw);
    const x = cosYaw * dx + sinYaw * dz;
    const zYaw = -sinYaw * dx + cosYaw * dz;
    const cosPitch = Math.cos(pitch);
    const sinPitch = Math.sin(pitch);
    const y = cosPitch * dy - sinPitch * zYaw;
    const depth = distance + sinPitch * dy + cosPitch * zYaw;
    if (depth <= 0.05) return null;
    const scaleFactor = camera.cameraType === 'orthographic'
        ? Math.min(width, height) * 0.22 * Number(camera.zoom ?? 1)
        : Math.min(width, height) * 0.42 * Number(camera.zoom ?? 1) / depth;
    return {
        x: width / 2 + Number(camera.offsetX ?? 0) + x * scaleFactor,
        y: height / 2 + Number(camera.offsetY ?? 0) - y * scaleFactor,
        depth,
    };
}

function drawProjectedLine(context, projection, points, color = GRID, width = 1) {
    const projected = points.map(projection);
    if (projected.some((point) => !point)) return;
    context.save();
    context.strokeStyle = color;
    context.lineWidth = width;
    context.beginPath();
    context.moveTo(projected[0].x, projected[0].y);
    projected.slice(1).forEach((point) => context.lineTo(point.x, point.y));
    context.stroke();
    context.restore();
}

function sampleVector(data, frame) {
    const values = Array.isArray(data) ? data : Array.isArray(data?.points) ? data.points : [];
    const value = values[Math.min(values.length - 1, frame)];
    if (Array.isArray(value) && value.length >= 3) return value.slice(0, 3).map(Number);
    if (value && typeof value === 'object') {
        const position = value.position ?? value.translation ?? value;
        if ([position.x, position.y, position.z].every((item) => Number.isFinite(Number(item)))) return [Number(position.x), Number(position.y), Number(position.z)];
    }
    return null;
}

function seriesLength(data) { return Array.isArray(data) ? data.length : Array.isArray(data?.points) ? data.points.length : 0; }
function rotateVector(quaternion, vector) { const [x, y, z, w] = quaternion; const q = [-x, -y, -z, w]; const p = [vector[0], vector[1], vector[2], 0]; return multiply(multiply(quaternion, p), q).slice(0, 3); }
function multiply(left, right) { const [x1, y1, z1, w1] = left; const [x2, y2, z2, w2] = right; return [w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2, w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2, w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2]; }
function add(left, right) { return left.map((value, index) => value + right[index]); }
function scale(value, factor) { return value.map((item) => item * factor); }
function subtract(left, right) { return left.map((value, index) => value - right[index]); }
function sampleScalar(data, frame) {
    const values = Array.isArray(data) ? data : Array.isArray(data?.points) ? data.points : [];
    const item = values[Math.min(values.length - 1, Math.max(0, frame))];
    if (Number.isFinite(Number(item))) return Number(item);
    if (item && typeof item === 'object') return Number(item.value ?? item.contact ?? item.active);
    return Number.NaN;
}
function drawArrow(context, projection, start, end, color, width) {
    const first = projection(start);
    const second = projection(end);
    if (!first || !second) return;
    context.save();
    context.strokeStyle = color;
    context.fillStyle = color;
    context.lineWidth = width;
    context.beginPath();
    context.moveTo(first.x, first.y);
    context.lineTo(second.x, second.y);
    context.stroke();
    const angle = Math.atan2(second.y - first.y, second.x - first.x);
    context.beginPath();
    context.moveTo(second.x, second.y);
    context.lineTo(second.x - 7 * Math.cos(angle - 0.45), second.y - 7 * Math.sin(angle - 0.45));
    context.lineTo(second.x - 7 * Math.cos(angle + 0.45), second.y - 7 * Math.sin(angle + 0.45));
    context.closePath();
    context.fill();
    context.restore();
}
