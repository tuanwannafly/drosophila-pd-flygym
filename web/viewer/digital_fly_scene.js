import * as THREE from 'three';
import { addViewerLighting } from './lighting.js';

export class DigitalFlyScene {
    constructor() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x0b0f14);
        this.scene.fog = new THREE.Fog(0x0b0f14, 18, 48);
        this.root = new THREE.Group();
        this.root.name = 'digital-fly-root';
        this.scene.add(this.root);

        this.ground = new THREE.Mesh(
            new THREE.PlaneGeometry(48, 48),
            new THREE.MeshStandardMaterial({ color: 0x151b20, roughness: 0.92, metalness: 0 }),
        );
        this.ground.position.z = 0;
        this.ground.name = 'ground';
        this.ground.receiveShadow = true;
        this.scene.add(this.ground);
        this.grid = new THREE.GridHelper(48, 48, 0x4a5b66, 0x27343d);
        this.grid.name = 'grid';
        this.grid.rotation.x = Math.PI / 2;
        this.grid.position.z = 0.002;
        this.scene.add(this.grid);
        this.axes = new THREE.AxesHelper(2);
        this.axes.name = 'axes';
        this.scene.add(this.axes);
        this.lights = addViewerLighting(this.scene);
        this.shadowEnabled = true;
    }

    setGroundVisible(visible) { this.ground.visible = Boolean(visible); }
    setGridVisible(visible) { this.grid.visible = Boolean(visible); }
    setAxesVisible(visible) { this.axes.visible = Boolean(visible); }
    setShadowEnabled(visible) {
        this.shadowEnabled = Boolean(visible);
        this.ground.receiveShadow = this.shadowEnabled;
        Object.values(this.lights).forEach((light) => {
            if ('castShadow' in light) light.castShadow = this.shadowEnabled && light.name === 'key-light';
        });
    }

    dispose() {
        this.scene.traverse((object) => {
            object.geometry?.dispose?.();
            if (Array.isArray(object.material)) object.material.forEach((material) => material.dispose?.());
            else object.material?.dispose?.();
        });
    }
}
