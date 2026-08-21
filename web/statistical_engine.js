import { describe, distribution } from './statistical_descriptive.js';
import { bootstrapStatistic, jackknife } from './statistical_resampling.js';
import { welchTTest, mannWhitney, wilcoxonSignedRank, kolmogorovSmirnov, permutationTest } from './statistical_tests.js';
import { effectSizes } from './statistical_effects.js';
import { adjustPValues } from './statistical_corrections.js';
import { pearson, spearman, kendall, partialCorrelation, correlationMatrix } from './statistical_correlation.js';
import { linearRegression, polynomialRegression, robustRegression, residualAnalysis } from './statistical_regression.js';
import { checkAssumptions } from './statistical_validation.js';
import { StatisticalReport } from './statistical_report.js';

export class StatisticalEngine {
    constructor(options = {}) { this.options = { ...options }; this.cache = new Map(); }

    describe(values, options = {}) { return this.cached('describe', values, options, () => ({ ...describe(values, options), distribution: distribution(values, options.bins ?? 10) })); }
    bootstrap(values, statistic, options = {}) { return bootstrapStatistic(values, statistic, options); }
    jackknife(values, statistic) { return jackknife(values, statistic); }
    tTest(left, right) { return welchTTest(left, right); }
    mannWhitney(left, right) { return mannWhitney(left, right); }
    wilcoxon(left, right) { return wilcoxonSignedRank(left, right); }
    ksTest(left, right = null) { return kolmogorovSmirnov(left, right); }
    permutation(left, right, statistic, options = {}) { return permutationTest(left, right, statistic, options); }
    effectSize(left, right) { return effectSizes(left, right); }
    adjust(pValues, method) { return adjustPValues(pValues, method); }
    correlation(left, right, method = 'pearson', controls = []) { return method === 'spearman' ? spearman(left, right) : method === 'kendall' ? kendall(left, right) : method === 'partial' ? partialCorrelation(left, right, controls) : pearson(left, right); }
    correlations(columns) { return correlationMatrix(columns); }
    regression(x, y, method = 'linear', options = {}) { const model = method === 'polynomial' ? polynomialRegression(x, y, options.degree ?? 2) : method === 'robust' ? robustRegression(x, y, options) : linearRegression(x, y); return { ...model, residualAnalysis: residualAnalysis(model) }; }
    validate(left, right = null, options = {}) { return checkAssumptions(left, right, options); }

    compare(left, right, options = {}) {
        const results = [
            { name: 't-test', ...this.tTest(left, right) },
            { name: 'mann-whitney', ...this.mannWhitney(left, right) },
            { name: 'effect-size', ...this.effectSize(left, right) },
        ];
        const pValues = results.map((result) => result.pValue ?? result.pValueApprox);
        return { results, corrections: this.adjust(pValues, options.correction ?? 'holm'), validation: this.validate(left, right, options) };
    }

    report(analyses = [], metadata = {}) {
        const report = { version: 1, title: metadata.title ?? 'Statistical Analysis Report', scope: 'Computational statistical analysis only; no biological interpretation is implied.', generatedAt: new Date().toISOString(), analysisCount: analyses.length, results: analyses, provenance: { ...metadata } };
        return { ...report, markdown: StatisticalReport.toMarkdown(report), html: StatisticalReport.toHTML(report), csv: StatisticalReport.toCSV(report), json: StatisticalReport.toJSON(report) };
    }

    benchmark(values, options = {}) {
        const start = performanceNow(); const iterations = options.iterations ?? 10; let result = null;
        for (let index = 0; index < iterations; index += 1) result = this.describe(values);
        return { iterations, sampleCount: values.length, elapsedMs: performanceNow() - start, resultAvailable: Boolean(result?.available) };
    }

    clear() { this.cache.clear(); }
    cached(prefix, values, options, factory) { const key = `${prefix}:${JSON.stringify([values, options])}`; if (!this.cache.has(key)) this.cache.set(key, factory()); return this.cache.get(key); }
}

export { describe, bootstrapStatistic, jackknife, welchTTest, mannWhitney, wilcoxonSignedRank, kolmogorovSmirnov, permutationTest, effectSizes, adjustPValues, pearson, spearman, kendall, partialCorrelation, correlationMatrix, linearRegression, polynomialRegression, robustRegression, residualAnalysis, checkAssumptions };

function performanceNow() { return typeof performance !== 'undefined' && performance.now ? performance.now() : Date.now(); }
