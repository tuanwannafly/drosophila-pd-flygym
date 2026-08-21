import { finiteValues, mean } from './statistical_math.js';

export function linearRegression(x, y) { return fitRegression(x, y, 1, 'linear'); }
export function polynomialRegression(x, y, degree = 2) { return fitRegression(x, y, Math.max(1, Math.floor(degree)), 'polynomial'); }

export function robustRegression(x, y, options = {}) {
    let result = polynomialRegression(x, y, options.degree ?? 1);
    const iterations = options.iterations ?? 10;
    for (let iteration = 0; iteration < iterations; iteration += 1) {
        const residuals = result.residuals; const scale = medianAbsoluteDeviation(residuals) || 1;
        const weights = residuals.map((residual) => Math.min(1, (options.tuning ?? 1.345) * scale / Math.max(scale, Math.abs(residual))));
        result = fitRegression(x, y, options.degree ?? 1, 'robust', weights);
    }
    return { ...result, method: 'robust-irls', iterations };
}

export function residualAnalysis(model) {
    const residuals = model?.residuals ?? [];
    return { count: residuals.length, mean: mean(residuals), sumSquared: residuals.reduce((sum, value) => sum + value ** 2, 0), absoluteMean: residuals.length ? residuals.reduce((sum, value) => sum + Math.abs(value), 0) / residuals.length : null, residuals };
}

function fitRegression(x, y, degree, method, weights = null) {
    const pairs = finiteValues(x).map((value, index) => [value, Number(y[index])]).filter(([, value]) => Number.isFinite(value));
    if (pairs.length <= degree) return { available: false, method, coefficients: [], predictions: [], residuals: [], rSquared: null };
    const design = pairs.map(([value]) => Array.from({ length: degree + 1 }, (_, power) => value ** power));
    const target = pairs.map(([, value]) => value);
    const coefficients = solveNormalEquations(design, target, weights);
    const predictions = design.map((row) => row.reduce((sum, value, index) => sum + value * coefficients[index], 0));
    const residuals = target.map((value, index) => value - predictions[index]); const targetMean = mean(target);
    const total = target.reduce((sum, value) => sum + (value - targetMean) ** 2, 0); const residual = residuals.reduce((sum, value) => sum + value ** 2, 0);
    return { available: true, method, degree, coefficients, predictions, residuals, rSquared: total ? 1 - residual / total : null, sampleCount: pairs.length };
}

function solveNormalEquations(design, target, weights = null) {
    const size = design[0].length; const matrix = Array.from({ length: size }, () => Array(size + 1).fill(0));
    design.forEach((row, rowIndex) => { const weight = weights?.[rowIndex] ?? 1; for (let i = 0; i < size; i += 1) { for (let j = 0; j < size; j += 1) matrix[i][j] += weight * row[i] * row[j]; matrix[i][size] += weight * row[i] * target[rowIndex]; } });
    for (let column = 0; column < size; column += 1) { let pivot = column; for (let row = column + 1; row < size; row += 1) if (Math.abs(matrix[row][column]) > Math.abs(matrix[pivot][column])) pivot = row; [matrix[column], matrix[pivot]] = [matrix[pivot], matrix[column]]; const divisor = matrix[column][column] || 1e-12; for (let j = column; j <= size; j += 1) matrix[column][j] /= divisor; for (let row = 0; row < size; row += 1) if (row !== column) { const factor = matrix[row][column]; for (let j = column; j <= size; j += 1) matrix[row][j] -= factor * matrix[column][j]; } }
    return matrix.map((row) => row[size]);
}

function medianAbsoluteDeviation(values) { const sorted = [...values].sort((a, b) => a - b); const median = sorted[Math.floor(sorted.length / 2)] ?? 0; const deviations = sorted.map((value) => Math.abs(value - median)).sort((a, b) => a - b); return deviations[Math.floor(deviations.length / 2)] ?? 0; }
