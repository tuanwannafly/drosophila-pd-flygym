import * as THREE from 'three';

export function addViewerLighting(scene) {
    const ambient = new THREE.AmbientLight(0x8aa0b8, 0.45);
    ambient.name = 'ambient-light';
    const hemisphere = new THREE.HemisphereLight(0xe3f4ff, 0x1c1713, 1.35);
    hemisphere.name = 'hemisphere-light';
    const key = new THREE.DirectionalLight(0xffffff, 2.2);
    key.position.set(4.5, 7.5, 5.5);
    key.name = 'key-light';
    key.castShadow = true;
    key.shadow.mapSize.width = 2048;
    key.shadow.mapSize.height = 2048;
    key.shadow.camera.near = 0.5;
    key.shadow.camera.far = 50;
    key.shadow.camera.left = -10;
    key.shadow.camera.right = 10;
    key.shadow.camera.top = 10;
    key.shadow.camera.bottom = -10;
    key.shadow.bias = -0.0002;
    const fill = new THREE.DirectionalLight(0x8fb4ff, 0.65);
    fill.position.set(-4, 3, -3);
    fill.name = 'fill-light';
    const rim = new THREE.DirectionalLight(0xffd7a8, 0.55);
    rim.position.set(-2, 4, 5);
    rim.name = 'rim-light';
    scene.add(ambient, hemisphere, key, fill, rim);
    return { ambient, hemisphere, key, fill, rim };
}
