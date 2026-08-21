import * as THREE from 'three';
import { vectorFromValue } from './joint_animator.js';

/** Draws explicit joint positions from imported pose data or DigitalFly3D snapshots. */
export class SkeletonRenderer {
    constructor() {
        this.group = new THREE.Group();
        this.group.name = 'skeleton-overlay';
        this.visible = true;
        this.jointGeometry = new THREE.SphereGeometry(0.07, 12, 8);
        this.jointMaterial = new THREE.MeshStandardMaterial({ color: 0xf0b429 });
        this.boneMaterial = new THREE.LineBasicMaterial({ color: 0x58c4dd });
    }

    clear() {
        while (this.group.children.length) {
            const child = this.group.children[0];
            this.group.remove(child);
            child.geometry?.dispose?.();
            child.material?.dispose?.();
        }
    }

    updateFromPoseFrame(frame) {
        this.clear();
        const source = frame?.skeleton?.bones ?? frame?.joint_positions ?? frame?.joints ?? frame?.trajectory?.joints ?? null;
        const positions = new Map();
        if (Array.isArray(source)) source.forEach((item) => { const p = vectorFromValue(item?.position ?? item); if (p && item?.id) positions.set(item.id, { position: p, parentId: item.parentId }); });
        else if (source) Object.entries(source).forEach(([id, value]) => { const p = vectorFromValue(value?.position ?? value); if (p) positions.set(id, { position: p, parentId: value?.parentId }); });
        if (positions.size) this._drawPositions(positions);
        const com = vectorFromValue(frame?.COM);
        if (com) this._drawMarker(com, 0x7ee787, 'COM');
    }

    updateFromSnapshot(snapshot) {
        this.clear();
        const positions = new Map((snapshot?.bones ?? []).map((bone) => [
            bone.id,
            { position: vectorFromValue(bone.worldTransform?.translation), parentId: bone.parentId },
        ]).filter(([, value]) => value.position));
        this._drawPositions(positions);
        const com = vectorFromValue(snapshot?.com);
        if (com) this._drawMarker(com, 0x7ee787, 'COM');
    }

    _drawPositions(positions) {
        positions.forEach(({ position }, id) => this._drawMarker(position, 0xf0b429, id));
        positions.forEach(({ position, parentId }, id) => {
            const parent = positions.get(parentId);
            if (!parent || !parent.position) return;
            const geometry = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(...parent.position), new THREE.Vector3(...position),
            ]);
            const line = new THREE.Line(geometry, this.boneMaterial.clone());
            line.name = `bone:${id}`;
            this.group.add(line);
        });
    }

    _drawMarker(position, color, name) {
        const marker = new THREE.Mesh(this.jointGeometry.clone(), this.jointMaterial.clone());
        marker.material.color.setHex(color);
        marker.position.set(...position);
        marker.name = name;
        marker.userData.joint = name;
        this.group.add(marker);
    }

    setVisible(visible) { this.visible = Boolean(visible); this.group.visible = this.visible; }

    dispose() {
        this.clear();
        this.jointGeometry.dispose();
        this.jointMaterial.dispose();
        this.boneMaterial.dispose();
        this.group.removeFromParent();
    }
}
