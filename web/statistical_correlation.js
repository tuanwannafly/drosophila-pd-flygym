import { finiteValues, mean } from './statistical_math.js';

export function pearson(left, right) {
    const pairs = paired(left, right); if (pairs.length < 2) return null;
    const a = pairs.map(([x]) => x); const b = pairs.map(([, y]) => y); const meanA = mean(a); const meanB = mean(b);
    const numerator = pairs.reduce((sum, [x, y]) => sum + (x - meanA) * (y - meanB), 0);
    const denominator = Math.sqrt(a.reduce((sum, x) => sum + (x - meanA) ** 2, 0) * b.reduce((sum, y) => sum + (y - meanB) ** 2, 0));
    return denominator ? numerator / denominator : null;
}

export function spearman(left, right) { const pairs = paired(left, right); return pairs.length < 2 ? null : pearson(rank(pairs.map(([x]) => x)), rank(pairs.map(([, y]) => y))); }

export function kendall(left, right) {
    const pairs = paired(left, right); if (pairs.length < 2) return null; let concordant = 0; let discordant = 0;
    for (let i = 0; i < pairs.length; i += 1) for (let j = i + 1; j < pairs.length; j += 1) { const sign = (pairs[i][0] - pairs[j][0]) * (pairs[i][1] - pairs[j][1]); if (sign > 0) concordant += 1; else if (sign < 0) discordant += 1; }
    return (concordant - discordant) / (pairs.length * (pairs.length - 1) / 2);
}

export function partialCorrelation(x, y, controls = []) {
    const rows = [x, y, ...controls].map(finiteValues); const length = Math.min(...rows.map((row) => row.length));
    if (length < 3 || !controls.length) return pearson(x, y);
    const residualX = residualize(rows[0].slice(0, length), controls.map((row) => row.slice(0, length)));
    const residualY = residualize(rows[1].slice(0, length), controls.map((row) => row.slice(0, length)));
    return pearson(residualX, residualY);
}

export function correlationMatrix(columns = {}) {
    const names = Object.keys(columns);
    return { names, pearson: matrix(names, columns, pearson), spearman: matrix(names, columns, spearman), kendall: matrix(names, columns, kendall) };
}

function paired(left, right) { const a = finiteValues(left); const b = finiteValues(right); return Array.from({ length: Math.min(a.length, b.length) }, (_, index) => [a[index], b[index]]); }
function rank(values) { return values.map((value) => 1 + values.filter((other) => other < value).length + (values.filter((other) => other === value).length - 1) / 2); }
function matrix(names, columns, method) { return names.map((left) => names.map((right) => method(columns[left], columns[right]))); }
function residualize(target, controls) { const controlMean = controls.map((row) => mean(row)); const targetMean = mean(target); return target.map((value, index) => value - targetMean - controls.reduce((sum, row, controlIndex) => sum + (row[index] - controlMean[controlIndex]) / Math.max(1, controls.length), 0)); }
