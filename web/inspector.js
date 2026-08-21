export class Inspector {
    constructor(workspace, onChange = null) {
        this.workspace = workspace;
        this.container = null;
        this.onChange = onChange;
    }

    init(container) {
        this.container = container;
        this.render();
    }

    render() {
        if (!this.container) return;

        this.container.replaceChildren();
        const heading = document.createElement('h3');
        heading.textContent = 'Inspector';
        this.container.appendChild(heading);

        this.renderNodeSection();
        this.renderKeyframeSection();
    }

    renderNodeSection() {
        const heading = document.createElement('h4');
        heading.textContent = 'Node';
        this.container.appendChild(heading);

        const node = this.workspace.selectedNode;
        if (!node) {
            const emptyState = document.createElement('p');
            emptyState.className = 'inspector-empty';
            emptyState.textContent = 'No node selected';
            this.container.appendChild(emptyState);
            return;
        }

        const details = document.createElement('dl');
        appendDetail(details, 'Name', getNodeName(node));
        appendDetail(details, 'ID', getOptionalValue(node.id));
        appendDetail(details, 'Type', getOptionalValue(node.type ?? node.kind));
        appendDetail(details, 'Parent', getParentLabel(this.workspace.data, node));
        appendDetail(details, 'Children count', getChildren(node).length);
        this.container.appendChild(details);

        if (node.metadata !== undefined && node.metadata !== null) {
            const metadataHeading = document.createElement('h4');
            metadataHeading.textContent = 'Node Metadata';
            this.container.appendChild(metadataHeading);

            const metadata = document.createElement('pre');
            metadata.className = 'inspector-metadata';
            metadata.textContent = formatMetadata(node.metadata);
            this.container.appendChild(metadata);
        }
    }

    renderKeyframeSection() {
        const heading = document.createElement('h4');
        heading.textContent = 'Keyframe';
        this.container.appendChild(heading);

        const selectedKeyframe = this.workspace.selectedKeyframe;
        if (!selectedKeyframe) {
            const emptyState = document.createElement('p');
            emptyState.className = 'inspector-empty';
            emptyState.textContent = 'No keyframe selected';
            this.container.appendChild(emptyState);
            return;
        }

        const data = selectedKeyframe.data;
        const frameInput = appendInput(
            this.container,
            'Frame Number',
            selectedKeyframe.frame,
            'number',
            { min: 0, max: Math.max(0, this.workspace.totalFrames - 1), step: 1 },
        );
        frameInput.addEventListener('change', (event) => {
            this.workspace.updateSelectedKeyframeFrame(event.target.value);
            this.notifyChange();
        });

        const duration = getDurationField(this.workspace, data);
        if (duration) {
            const durationInput = appendInput(
                this.container,
                'Duration',
                duration.value,
                'number',
                { min: 0, step: 'any' },
            );
            durationInput.addEventListener('change', (event) => {
                this.workspace.updateSelectedKeyframeDuration(event.target.value);
                this.notifyChange();
            });
        }

        const readOnlyDetails = document.createElement('dl');
        appendDetail(readOnlyDetails, 'Node Count', getNodeCount(data));
        appendDetail(readOnlyDetails, 'Playback Time', getPlaybackTime(data));
        this.container.appendChild(readOnlyDetails);

        const metadataLabel = document.createElement('label');
        metadataLabel.className = 'inspector-field';
        metadataLabel.textContent = 'Metadata';
        const metadataInput = document.createElement('textarea');
        metadataInput.className = 'inspector-input inspector-textarea';
        metadataInput.value = getEditableMetadata(data);
        metadataInput.setAttribute('aria-label', 'Keyframe metadata');
        metadataInput.rows = 5;
        metadataLabel.appendChild(metadataInput);
        this.container.appendChild(metadataLabel);

        const metadataStatus = document.createElement('p');
        metadataStatus.className = 'inspector-status';
        this.container.appendChild(metadataStatus);
        metadataInput.addEventListener('change', (event) => {
            const result = parseMetadata(event.target.value);
            if (!result.valid) {
                metadataStatus.textContent = 'Metadata must be valid JSON.';
                return;
            }
            this.workspace.updateSelectedKeyframeMetadata(result.value);
            this.notifyChange();
        });
    }

    notifyChange() {
        if (this.onChange) {
            this.onChange();
        } else {
            this.render();
        }
    }
}

function appendInput(container, label, value, type, attributes = {}) {
    const field = document.createElement('label');
    field.className = 'inspector-field';
    field.textContent = label;
    const input = document.createElement('input');
    input.className = 'inspector-input';
    input.type = type;
    input.value = value;
    Object.entries(attributes).forEach(([key, attributeValue]) => {
        input.setAttribute(key, String(attributeValue));
    });
    field.appendChild(input);
    container.appendChild(field);
    return input;
}

function appendDetail(list, label, value) {
    const term = document.createElement('dt');
    term.textContent = label;
    const description = document.createElement('dd');
    description.textContent = String(value);
    list.appendChild(term);
    list.appendChild(description);
}

function getNodeName(node) {
    return node.name ?? node.id ?? node.type ?? node.kind ?? 'Unnamed node';
}

function getOptionalValue(value) {
    return value === undefined || value === null || value === ''
        ? 'Not available'
        : value;
}

function getChildren(node) {
    return Array.isArray(node.children) ? node.children : [];
}

function getParentLabel(data, target) {
    const parent = findParent(Array.isArray(data.nodes) ? data.nodes : [], target);
    if (!parent) return 'Scene root';
    return getNodeName(parent);
}

function findParent(nodes, target, parent = null) {
    for (const node of nodes) {
        if (!node || typeof node !== 'object') continue;
        if (node === target) return parent;
        const children = getChildren(node);
        const result = findParent(children, target, node);
        if (result) return result;
    }
    return null;
}

function formatMetadata(metadata) {
    if (typeof metadata === 'object') {
        try {
            return JSON.stringify(metadata, null, 2);
        } catch (error) {
            return String(metadata);
        }
    }
    return String(metadata);
}

function getDurationField(workspace, data) {
    if (data && typeof data === 'object' && data.duration !== undefined) {
        return { value: data.duration };
    }
    if (workspace.animation?.duration !== undefined) {
        return { value: workspace.animation.duration };
    }
    return null;
}

function getNodeCount(data) {
    if (!data || typeof data !== 'object') return 'Not available';
    if (Number.isInteger(data.nodeCount) && data.nodeCount >= 0) return data.nodeCount;
    if (Array.isArray(data.nodes)) return data.nodes.length;

    const mapping = data.nodeTransforms ?? data.transforms ?? data.positions;
    if (mapping && typeof mapping === 'object' && !Array.isArray(mapping)) {
        return Object.keys(mapping).length;
    }
    return 'Not available';
}

function getPlaybackTime(data) {
    if (!data || typeof data !== 'object' || data.time === undefined) {
        return 'Not available';
    }
    return data.time;
}

function getEditableMetadata(data) {
    if (!data || typeof data !== 'object' || data.metadata === undefined) return '';
    return formatMetadata(data.metadata);
}

function parseMetadata(text) {
    if (text.trim() === '') return { valid: true, value: undefined };
    try {
        return { valid: true, value: JSON.parse(text) };
    } catch (error) {
        return { valid: false, value: null };
    }
}
