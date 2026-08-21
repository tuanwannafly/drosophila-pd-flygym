export class JSONLoader {
    static validateScene(data) {
        if (!data || typeof data !== 'object' || Array.isArray(data)) {
            throw new Error('Scene JSON must contain an object.');
        }

        if (!Object.prototype.hasOwnProperty.call(data, 'scene')) {
            throw new Error('Scene JSON is missing the required "scene" field.');
        }

        if (!Array.isArray(data.nodes)) {
            throw new Error('Scene JSON must contain a "nodes" array.');
        }

        return data;
    }

    static async parseFile(file) {
        return JSONLoader.validateScene(await JSONLoader.parseRawFile(file));
    }

    static async parseRawFile(file) {
        if (!file) {
            throw new Error('No JSON file was selected.');
        }

        const fileName = file.name || '';
        if (!fileName.toLowerCase().endsWith('.json')) {
            throw new Error('Please select a file with a .json extension.');
        }

        let data;
        try {
            data = JSON.parse(await file.text());
        } catch (error) {
            throw new Error(`Invalid JSON: ${error.message}`);
        }
        return data;
    }

    static summarizeScene(data) {
        const nodes = flattenNodes(data.nodes);
        const cameras = getCollectionCount(data.cameras ?? data.scene?.cameras);
        const trajectories = getCollectionCount(
            data.trajectories ?? data.scene?.trajectories,
        );

        return {
            nodeCount: nodes.length,
            cameraCount: cameras || countTypedNodes(nodes, 'camera'),
            trajectoryCount: trajectories || countTypedNodes(nodes, 'trajectory'),
        };
    }

    static async loadJSON(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error("Failed to load JSON:", error);
            return null;
        }
    }
}

function flattenNodes(nodes) {
    return nodes.reduce((result, node) => {
        if (!node || typeof node !== 'object') return result;
        result.push(node);
        if (Array.isArray(node.children)) {
            result.push(...flattenNodes(node.children));
        }
        return result;
    }, []);
}

function getCollectionCount(collection) {
    if (Array.isArray(collection)) return collection.length;
    if (collection && typeof collection === 'object') return Object.keys(collection).length;
    return 0;
}

function countTypedNodes(nodes, type) {
    return nodes.filter((node) => {
        const nodeType = node.type ?? node.kind;
        return typeof nodeType === 'string' && nodeType.toLowerCase() === type;
    }).length;
}
