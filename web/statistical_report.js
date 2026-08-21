export class StatisticalReport {
    static toJSON(report, pretty = true) { return JSON.stringify(report, null, pretty ? 2 : 0); }
    static toMarkdown(report) {
        const lines = [`# ${report.title ?? 'Statistical Analysis Report'}`, '', report.scope ?? '', '', `Analyses: ${report.analysisCount ?? 0}`, '', '## Results', '', '| Analysis | Method | Statistic | p-value |', '| --- | --- | ---: | ---: |'];
        (report.results ?? []).forEach((result) => lines.push(`| ${result.name ?? ''} | ${result.method ?? ''} | ${format(result.statistic)} | ${format(result.pValue ?? result.pValueApprox)} |`));
        lines.push('', '## Scientific boundary', '', 'This is computational statistical analysis only. It does not establish biological validation, diagnosis, disease severity, dopamine equivalence, or mechanism.');
        return lines.join('\n');
    }
    static toHTML(report) { return `<article><h1>${escapeText(report.title ?? 'Statistical Analysis Report')}</h1><p>${escapeText(report.scope ?? '')}</p><pre>${escapeText(this.toJSON(report))}</pre></article>`; }
    static toCSV(report) { return [['name', 'method', 'statistic', 'p_value'], ...(report.results ?? []).map((result) => [result.name, result.method, result.statistic ?? '', result.pValue ?? result.pValueApprox ?? ''])].map((row) => row.map(csvCell).join(',')).join('\n'); }
}

function format(value) { return Number.isFinite(Number(value)) ? Number(value).toFixed(6) : ''; }
function csvCell(value) { const text = value === null || value === undefined ? '' : String(value); return /[,"\n]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text; }
function escapeText(value) { return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character])); }
