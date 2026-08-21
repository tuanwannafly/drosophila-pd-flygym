/** Read-only browser bridge for the model-free research assistant surface. */
export class AssistantBridge {
    constructor({ workspace, experimentWorkspace = null, laboratory = null } = {}) {
        this.workspace = workspace;
        this.experimentWorkspace = experimentWorkspace;
        this.laboratory = laboratory;
    }

    buildReport() {
        const datasets = this.experimentWorkspace?.datasets?.list?.() ?? [];
        const experiments = this.experimentWorkspace?.experiments?.list?.() ?? [];
        const validation = this.experimentWorkspace?.validation?.summarize?.() ?? null;
        const reports = this.laboratory?.reports?.list?.() ?? [];
        const warnings = [];
        if (!datasets.length && !this.workspace?.rollout) warnings.push('No dataset is loaded.');
        if (!validation) warnings.push('No validation summary is attached.');
        return {
            summary: {
                datasets: datasets.length,
                experiments: experiments.length,
                reports: reports.length,
                currentFrame: this.workspace?.currentFrame ?? 0,
                validation: validation?.status ?? 'UNAVAILABLE',
            },
            findings: [
                datasets.length ? 'Existing dataset records are available for review.' : 'No dataset records are available.',
                reports.length ? 'Existing report records are available for publication review.' : 'No report records are available.',
            ],
            warnings,
            recommendations: warnings.length
                ? ['Resolve missing source artifacts before interpreting or publishing results.']
                : ['Use the existing campaign matrix and preserve provenance for the next comparison.'],
            publication_notes: [
                'Use the original manuscript and report artifacts for publication wording.',
                'This browser panel summarizes computational artifacts and does not establish biological validity.',
            ],
        };
    }

    explainMetric(metric) {
        const key = String(metric ?? '').trim().toLowerCase();
        const explanations = {
            velocity: 'Speed or velocity already reported by the loaded analysis artifact.',
            acceleration: 'Change in a supplied velocity series over recorded time steps.',
            turning: 'Turning or yaw-derived values supplied by locomotion analysis.',
            freezing: 'Pause or immobility values supplied by behavioral assay output.',
        };
        return explanations[key] ?? 'No registered explanation is available for this metric artifact.';
    }

    explainChart(chart) {
        const key = String(chart ?? '').trim().toLowerCase();
        const explanations = {
            trajectory: 'A visual representation of supplied position samples over time.',
            speed: 'A chart of the supplied speed or velocity time series.',
            validation: 'A visual summary of supplied validation checks and errors.',
        };
        return explanations[key] ?? 'No registered explanation is available for this chart.';
    }

    explainValidation(validation = null) {
        const value = validation ?? this.experimentWorkspace?.validation?.summarize?.();
        if (value?.status === 'PASS' || value?.overall_pass === true) return 'The supplied validation summary reports pass for its declared checks.';
        if (value?.status === 'FAIL' || value?.overall_pass === false) return 'The supplied validation summary reports a failed check; inspect its details.';
        return 'No overall validation status is available.';
    }

    render(container) {
        container.replaceChildren();
        container.append(this.heading('Assistant', 'Read-only computational artifact summary'));
        const report = this.buildReport();
        this.section(container, 'Summary', Object.entries(report.summary).map(([key, value]) => `${key}: ${value}`));
        this.section(container, 'Findings', report.findings);
        this.section(container, 'Warnings', report.warnings.length ? report.warnings : ['None recorded.']);
        this.section(container, 'Recommendations', report.recommendations);
        this.section(container, 'Publication notes', report.publication_notes);
    }

    heading(title, subtitle) {
        const element = document.createElement('div');
        element.className = 'laboratory-section-heading';
        const titleElement = document.createElement('h3');
        titleElement.textContent = title;
        const subtitleElement = document.createElement('small');
        subtitleElement.textContent = subtitle;
        element.append(titleElement, subtitleElement);
        return element;
    }

    section(container, title, items) {
        const section = document.createElement('section');
        const heading = document.createElement('h4');
        heading.textContent = title;
        const list = document.createElement('ul');
        items.forEach((item) => {
            const entry = document.createElement('li');
            entry.textContent = item;
            list.append(entry);
        });
        section.append(heading, list);
        container.append(section);
    }
}
