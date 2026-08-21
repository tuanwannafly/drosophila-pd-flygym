export class ExperimentReportGenerator {
    constructor(experimentWorkspace, analyticsDashboard) {
        this.experimentWorkspace = experimentWorkspace;
        this.analyticsDashboard = analyticsDashboard;
    }

    build() {
        const analytics = this.analyticsDashboard.compute();
        return {
            version: 1,
            title: 'Fly Studio computational experiment summary',
            scope: 'This report describes computational rollouts; no biological validation is established.',
            generatedAt: new Date().toISOString(),
            experimentCount: this.experimentWorkspace.experiments.list().length,
            datasetValidation: this.experimentWorkspace.datasets.validate(),
            filters: { ...this.experimentWorkspace.filters },
            analytics,
            experiments: this.experimentWorkspace.experiments.list().map(({ id, name, kind, folder, tags, notes, metadata }) => ({ id, name, kind, folder, tags, notes, metadata })),
        };
    }

    toJSON() {
        return JSON.stringify(this.build(), null, 2);
    }

    toMarkdown() {
        const report = this.build();
        const lines = [
            `# ${report.title}`,
            '',
            report.scope,
            '',
            `Generated: ${report.generatedAt}`,
            `Experiments: ${report.experimentCount}`,
            `Rollouts: ${report.analytics.count}`,
            '',
            '## Metrics',
            '',
            '| Metric | Mean | Minimum | Maximum | Count |',
            '| --- | ---: | ---: | ---: | ---: |',
        ];
        Object.values(report.analytics.summary).forEach((metric) => {
            lines.push(`| ${metric.label} | ${format(metric.mean)} | ${format(metric.min)} | ${format(metric.max)} | ${metric.count} |`);
        });
        lines.push('', '## Dataset validation', '', `- Valid: ${report.datasetValidation.valid}`, `- Rows: ${report.datasetValidation.count}`, `- Missing: ${report.datasetValidation.missing.length}`, `- Duplicates: ${report.datasetValidation.duplicates.length}`);
        return lines.join('\n');
    }

    toHTML() {
        const markdown = this.toMarkdown();
        return `<article><pre>${escapeHTML(markdown)}</pre></article>`;
    }

    printPDF() {
        const popup = window.open('', '_blank');
        if (!popup) throw new Error('A popup is required for PDF printing.');
        popup.document.write(this.toHTML());
        popup.document.close();
        popup.focus();
        popup.print();
    }

    toCSV() {
        const report = this.build();
        const lines = ['metric,mean,min,max,count'];
        Object.values(report.analytics.summary).forEach((metric) => {
            lines.push([metric.label, metric.mean, metric.min, metric.max, metric.count].map(csv).join(','));
        });
        return lines.join('\n');
    }

    download(format) {
        const payloads = {
            json: [this.toJSON(), 'application/json', 'experiment-report.json'],
            markdown: [this.toMarkdown(), 'text/markdown', 'experiment-report.md'],
            html: [this.toHTML(), 'text/html', 'experiment-report.html'],
            csv: [this.toCSV(), 'text/csv', 'experiment-report.csv'],
        };
        const payload = payloads[format];
        if (!payload) throw new Error(`Unsupported report format: ${format}`);
        const link = document.createElement('a');
        link.href = URL.createObjectURL(new Blob([payload[0]], { type: payload[1] }));
        link.download = payload[2];
        link.click();
        URL.revokeObjectURL(link.href);
    }
}

function format(value) {
    return Number.isFinite(value) ? value.toFixed(6) : 'n/a';
}

function csv(value) {
    const text = value === null || value === undefined ? '' : String(value);
    return /[,"\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
}
