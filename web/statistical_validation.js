import { finiteValues, mean, standardDeviation, normalCDF } from './statistical_math.js';
import { detectOutliers } from './analysis_outliers.js';

export function checkAssumptions(left, right = null, options = {}) {
    const a = finiteValues(left); const b = right === null ? null : finiteValues(right);
    return {
        version: 1,
        scope: 'Computational statistical assumption checks only; no biological interpretation is implied.',
        missingData: { left: (Array.isArray(left) ? left.length : 0) - a.length, right: b ? (Array.isArray(right) ? right.length : 0) - b.length : null },
        normality: { left: normality(a), right: b ? normality(b) : null },
        varianceEquality: b ? varianceEquality(a, b) : null,
        outlierSensitivity: { left: detectOutliers(a, options.outlierOptions), right: b ? detectOutliers(b, options.outlierOptions) : null },
    };
}

function normality(values) {
    if (values.length < 3) return { available: false, reason: 'At least three observations are required.' };
    const center = mean(values); const std = standardDeviation(values, true) || 1; const skew = values.reduce((sum, value) => sum + ((value - center) / std) ** 3, 0) / values.length; const kurtosis = values.reduce((sum, value) => sum + ((value - center) / std) ** 4, 0) / values.length - 3; const statistic = values.length / 6 * (skew ** 2 + kurtosis ** 2 / 4);
    return { available: true, method: 'jarque-bera-approximation', statistic, pValueApprox: 1 - normalCDF(Math.sqrt(Math.max(0, statistic))), skewness: skew, excessKurtosis: kurtosis };
}

function varianceEquality(left, right) {
    if (left.length < 2 || right.length < 2) return { available: false };
    const leftVariance = standardDeviation(left, true) ** 2; const rightVariance = standardDeviation(right, true) ** 2; const ratio = leftVariance >= rightVariance ? leftVariance / (rightVariance || 1e-12) : rightVariance / (leftVariance || 1e-12);
    return { available: true, method: 'variance-ratio-screen', ratio, conservativeFlag: ratio > 4 };
}
