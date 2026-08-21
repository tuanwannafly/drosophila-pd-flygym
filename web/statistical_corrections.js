export function adjustPValues(pValues, method = 'holm') {
    const values = pValues.map((value) => Number(value));
    if (!['bonferroni', 'holm', 'benjamini-hochberg'].includes(method)) throw new Error(`Unsupported multiple-comparison correction: ${method}`);
    const indexed = values.map((value, index) => ({ value: Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : null, index })).filter((item) => item.value !== null).sort((a, b) => a.value - b.value);
    const adjusted = Array(values.length).fill(null);
    if (method === 'bonferroni') indexed.forEach((item) => { adjusted[item.index] = Math.min(1, item.value * indexed.length); });
    if (method === 'holm') indexed.forEach((item, rank) => { adjusted[item.index] = Math.min(1, item.value * (indexed.length - rank)); });
    if (method === 'benjamini-hochberg') {
        let running = 1;
        [...indexed].reverse().forEach((item, reverseRank) => {
            const rank = indexed.length - reverseRank;
            running = Math.min(running, item.value * indexed.length / rank);
            adjusted[item.index] = Math.min(1, running);
        });
    }
    return { method, count: indexed.length, adjusted, falseDiscoveryRate: method === 'benjamini-hochberg' ? 'controlled in the configured computational procedure' : null };
}
