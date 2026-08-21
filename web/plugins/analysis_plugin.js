export const analysisPlugin = {
    manifest: {
        id: 'flystudio.example.analysis',
        name: 'Analysis Plugin Example',
        version: '1.0.0',
        author: 'Fly Studio contributors',
        description: 'Example analysis extension boundary for caller-supplied analysis input.',
        dependencies: [],
        capabilities: ['analysis'],
    },
    run(input, context) {
        return { input, pluginId: context.plugin.id };
    },
    hooks: {
        onAnalysis(payload) {
            return payload;
        },
    },
};
