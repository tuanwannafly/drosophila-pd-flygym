import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { quaternionFromOrientation, vectorFromValue } from './joint_animator.js';

const MATERIAL_COLORS = Object.freeze({
    thorax: 0xd08a53,
    abdomen: 0x7c5039,
    head: 0xc98c5f,
    eye: 0x21130f,
    wing: 0xbfe6f5,
    leg: 0x3d2c24,
    antenna: 0x4a2f25,
});

/** Display mesh for imported rollout pose data.
 *
 * If a future viewer_pose.json declares a real GLTF/GLB asset, the mesh loader
 * uses it. Otherwise the viewer falls back to a clearly labeled presentation
 * mesh made from Three.js primitives. The fallback is visual only and does not
 * invent anatomical measurements.
 */
export class DigitalFlyMesh {
    constructor() {
        this.group = new THREE.Group();
        this.group.name = 'digital-fly-mesh';
        this.parts = new Map();
        this.metadata = null;
        this.usingFallback = true;
        this._buildFallback();
    }

    async loadMetadata(metadata = {}) {
        this.metadata = metadata ?? {};
        const loaded = await this._loadAsset(this.metadata.asset);
        if (!loaded) this._buildFallback();
        return this;
    }

    useFallback() {
        this.metadata = null;
        this._buildFallback();
        return this;
    }

    async _loadAsset(asset) {
        if (!asset || typeof asset.uri !== 'string' || !asset.uri) return false;
        try {
            const loader = new GLTFLoader();
            const gltf = await loader.loadAsync(asset.uri);
            this.clear();
            const root = gltf.scene;
            root.name = asset.name || 'digital-fly-gltf-mesh';
            root.traverse((object) => {
                if (!object.isMesh) return;
                object.castShadow = true;
                object.receiveShadow = true;
                if (!object.material) object.material = this._material('thorax');
                this.parts.set(object.name || `mesh:${this.parts.size}`, object);
            });
            this.group.add(root);
            this.usingFallback = false;
            return true;
        } catch (error) {
            console.warn('Unable to load declared fly mesh asset; using presentation fallback.', error);
            return false;
        }
    }

    _buildFallback() {
        this.clear();
        this.usingFallback = true;
        this._addEllipsoid('thorax', 'thorax', [0, 0, 0.03], [0.55, 0.36, 0.42]);
        this._addEllipsoid('abdomen', 'abdomen', [-0.72, 0, -0.02], [0.78, 0.39, 0.34], [0, 0.05, 0]);
        this._addEllipsoid('head', 'head', [0.62, 0, 0.1], [0.38, 0.32, 0.3]);
        this._addEllipsoid('eye_L', 'eye', [0.78, 0.22, 0.18], [0.09, 0.07, 0.08]);
        this._addEllipsoid('eye_R', 'eye', [0.78, -0.22, 0.18], [0.09, 0.07, 0.08]);
        this._addWing(1);
        this._addWing(-1);
        this._addAntenna(1);
        this._addAntenna(-1);
        [
            ['F', 0.38, 0.12],
            ['M', 0.0, 0.02],
            ['H', -0.38, -0.08],
        ].forEach(([pair, x, sweep]) => {
            this._addLeg(`L${pair}`, 1, x, sweep);
            this._addLeg(`R${pair}`, -1, x, sweep);
        });
    }

    clear() {
        while (this.group.children.length) {
            const child = this.group.children[0];
            this.group.remove(child);
            child.traverse?.((object) => {
                object.geometry?.dispose?.();
                if (Array.isArray(object.material)) object.material.forEach((material) => material.dispose?.());
                else object.material?.dispose?.();
            });
        }
        this.parts.clear();
    }

    _material(name, overrides = {}) {
        const transparent = name === 'wing' || overrides.opacity !== undefined;
        return new THREE.MeshStandardMaterial({
            color: MATERIAL_COLORS[name] ?? 0xffffff,
            roughness: name === 'wing' ? 0.35 : 0.82,
            metalness: 0.02,
            transparent,
            opacity: name === 'wing' ? 0.42 : 0.96,
            side: name === 'wing' ? THREE.DoubleSide : THREE.FrontSide,
            ...overrides,
        });
    }

    _addEllipsoid(id, materialName, position, scale, rotation = [0, 0, 0]) {
        const mesh = new THREE.Mesh(
            new THREE.SphereGeometry(1, 40, 24),
            this._material(materialName),
        );
        mesh.name = id;
        mesh.position.set(...position);
        mesh.rotation.set(...rotation);
        mesh.scale.set(...scale);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData.bodyPart = id;
        this.group.add(mesh);
        this.parts.set(id, mesh);
        return mesh;
    }

    _addWing(side) {
        const shape = new THREE.Shape();
        shape.moveTo(-0.18, 0);
        shape.bezierCurveTo(0.1, 0.32, 0.82, 0.35, 1.08, 0.04);
        shape.bezierCurveTo(0.84, -0.18, 0.18, -0.18, -0.18, 0);
        const mesh = new THREE.Mesh(
            new THREE.ShapeGeometry(shape, 20),
            this._material('wing', { depthWrite: false }),
        );
        mesh.name = side > 0 ? 'wing_L' : 'wing_R';
        mesh.position.set(-0.06, side * 0.35, 0.28);
        mesh.rotation.set(0.16, 0.04, side * 0.48);
        mesh.scale.set(0.92, side, 1);
        mesh.castShadow = false;
        mesh.receiveShadow = true;
        mesh.userData.bodyPart = 'wings';
        this.group.add(mesh);
        this.parts.set(mesh.name, mesh);
    }

    _addAntenna(side) {
        const start = [0.88, side * 0.11, 0.25];
        const end = [1.22, side * 0.26, 0.42];
        this._addCylinderBetween(`antenna_${side > 0 ? 'L' : 'R'}`, start, end, 0.015, 'antenna');
    }

    _addLeg(label, side, x, sweep) {
        const hip = [x, side * 0.28, -0.16];
        const knee = [x + sweep, side * 0.72, -0.44];
        const foot = [x + sweep * 1.4, side * 1.08, -0.72];
        this._addCylinderBetween(`leg_${label}_femur`, hip, knee, 0.035, 'leg', 'legs');
        this._addCylinderBetween(`leg_${label}_tibia`, knee, foot, 0.025, 'leg', 'legs');
        const footMesh = this._addEllipsoid(`leg_${label}_foot`, 'leg', foot, [0.07, 0.035, 0.025]);
        footMesh.userData.bodyPart = 'legs';
    }

    _addCylinderBetween(id, start, end, radius, materialName, bodyPart = materialName) {
        const a = new THREE.Vector3(...start);
        const b = new THREE.Vector3(...end);
        const midpoint = a.clone().add(b).multiplyScalar(0.5);
        const direction = b.clone().sub(a);
        const length = direction.length();
        const mesh = new THREE.Mesh(
            new THREE.CylinderGeometry(radius, radius, length, 12),
            this._material(materialName),
        );
        mesh.name = id;
        mesh.position.copy(midpoint);
        mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.normalize());
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData.bodyPart = bodyPart;
        this.group.add(mesh);
        this.parts.set(id, mesh);
        return mesh;
    }

    updateFromFrame(frame) {
        const thorax = vectorFromValue(frame?.thorax);
        if (thorax) this.group.position.set(...thorax);
        const orientation = quaternionFromOrientation(frame?.orientation);
        if (orientation) this.group.quaternion.copy(orientation);
    }

    updateFromSnapshot(snapshot) {
        const thorax = snapshot?.bones?.find((bone) => bone.id === 'thorax');
        const position = thorax?.worldTransform?.translation;
        if (Array.isArray(position)) this.group.position.set(...position);
    }

    setPartVisibility(part, visible) {
        this.parts.forEach((mesh) => {
            if (mesh.userData.bodyPart === part || mesh.name === part || mesh.name.startsWith(`${part}_`)) {
                mesh.visible = Boolean(visible);
            }
        });
    }

    setOpacity(opacity) {
        this.parts.forEach((mesh) => {
            if (!mesh.material) return;
            mesh.material.transparent = true;
            mesh.material.opacity = Math.max(0, Math.min(1, Number(opacity) || 0));
        });
    }

    setShadows(enabled) {
        this.group.traverse((object) => {
            if (object.isMesh) {
                object.castShadow = Boolean(enabled) && object.userData.bodyPart !== 'wings';
                object.receiveShadow = Boolean(enabled);
            }
        });
    }

    dispose() {
        this.clear();
        this.group.removeFromParent();
    }
}
