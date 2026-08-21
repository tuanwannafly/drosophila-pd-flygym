export const statisticsPlugin = {
    manifest: {
        id: 'flystudio.example.statistics',
        name: 'Statistics Plugin Example',
        version: '1.0.0',
        author: 'Fly Studio contributors',
        description: 'Example statistics extension boundary for caller-supplied summaries.',
        dependencies: [],
        capabilities: ['statistics'],
    },
    run(input, context) {
        return { input, pluginId: context.plugin.id };
    },
    hooks: {
        onStatistics(payload) {
            return payload;
        },
    },
};
