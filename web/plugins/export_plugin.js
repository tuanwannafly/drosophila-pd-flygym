export const exportPlugin = {
    manifest: {
        id: 'flystudio.example.export',
        name: 'Export Plugin Example',
        version: '1.0.0',
        author: 'Fly Studio contributors',
        description: 'Example export extension boundary for caller-supplied report data.',
        dependencies: [],
        capabilities: ['export'],
    },
    run(input, context) {
        return { input, pluginId: context.plugin.id };
    },
    hooks: {
        onExport(payload) {
            return payload;
        },
    },
};
