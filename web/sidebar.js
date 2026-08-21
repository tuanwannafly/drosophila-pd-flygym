import { JSONLoader } from './json_loader.js';

export class Sidebar {
    constructor({ onSelectNode = null } = {}) {
        this.container = null;
        this.onSelectNode = onSelectNode;
    }

    init(container) {
        this.container = container;
        this.render();
    }

    render(data = {}, selectedNode = null) {
        if (!this.container) return;
        const summary = Array.isArray(data.nodes)
            ? JSONLoader.summarizeScene(data)
            : { nodeCount: 0, cameraCount: 0, trajectoryCount: 0 };
        const cameras = countCollection(data.cameras ?? data.scene?.cameras);
        const trajectories = countCollection(data.trajectories ?? data.scene?.trajectories);
        this.container.innerHTML = `
            <h3>Project Explorer</h3>
            <ul class="project-summary">
                <li>Assets <span>${countCollection(data.assets)}</span></li>
                <li>Scenes <span>${data.scene ? 1 : 0}</span></li>
                <li>Nodes <span>${summary.nodeCount}</span></li>
                <li>Cameras <span>${cameras || summary.cameraCount}</span></li>
                <li>Trajectories <span>${trajectories || summary.trajectoryCount}</span></li>
            </ul>
            <section class="scene-tree-panel" aria-labelledby="scene-tree-title">
                <h4 id="scene-tree-title"></h4>
                <div class="scene-tree-content"></div>
            </section>
        `;

        const sceneTitle = this.container.querySelector('#scene-tree-title');
        sceneTitle.textContent = getSceneLabel(data.scene);
        const treeContent = this.container.querySelector('.scene-tree-content');
        const nodes = Array.isArray(data.nodes) ? data.nodes : [];
        if (nodes.length === 0) {
            const emptyState = document.createElement('p');
            emptyState.className = 'scene-tree-empty';
            emptyState.textContent = 'No scene nodes loaded.';
            treeContent.appendChild(emptyState);
            return;
        }

        const tree = document.createElement('ul');
        tree.className = 'scene-tree';
        appendNodes(tree, nodes, selectedNode, this.onSelectNode);
        treeContent.appendChild(tree);
    }
}

function appendNodes(list, nodes, selectedNode, onSelectNode) {
    nodes.forEach((node) => {
        const element = createNodeElement(node, selectedNode, onSelectNode);
        if (element) list.appendChild(element);
    });
}

function createNodeElement(node, selectedNode, onSelectNode) {
    if (!node || typeof node !== 'object' || Array.isArray(node)) return null;

    const item = document.createElement('li');
    item.className = 'scene-tree-node';
    if (node === selectedNode) item.classList.add('selected');
    const children = Array.isArray(node.children)
        ? node.children.filter((child) => child && typeof child === 'object')
        : [];

    if (children.length === 0) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'scene-tree-node-label';
        button.textContent = getNodeLabel(node);
        button.addEventListener('click', () => {
            if (onSelectNode) onSelectNode(node);
        });
        item.appendChild(button);
        return item;
    }

    const details = document.createElement('details');
    details.open = true;
    const label = document.createElement('summary');
    label.textContent = getNodeLabel(node);
    label.addEventListener('click', () => {
        if (onSelectNode) onSelectNode(node);
    });
    details.appendChild(label);

    const childList = document.createElement('ul');
    appendNodes(childList, children, selectedNode, onSelectNode);
    details.appendChild(childList);
    item.appendChild(details);
    return item;
}

function getNodeLabel(node) {
    return String(node.name ?? node.id ?? node.type ?? node.kind ?? 'Unnamed node');
}

function getSceneLabel(scene) {
    if (scene && typeof scene === 'object' && scene.name) return String(scene.name);
    return 'Scene';
}

function countCollection(collection) {
    if (Array.isArray(collection)) return collection.length;
    if (collection && typeof collection === 'object') return Object.keys(collection).length;
    return 0;
}
