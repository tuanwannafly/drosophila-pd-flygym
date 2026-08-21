const LABELS = Object.freeze(['Walking', 'Turning', 'Standing', 'Grooming', 'Unknown']);

export const BEHAVIOR_LABELS = LABELS;

export function segmentBehavior(features, options = {}) {
    const speedThreshold = Number(options.speedThreshold ?? 1e-4);
    const turnThreshold = Number(options.turnRateThreshold ?? 0.1);
    const length = Math.max(features?.timeseries?.speed?.length ?? 0, features?.timeseries?.turningRate?.length ?? 0);
    const labels = Array.from({ length }, (_, frame) => labelFrame(features, frame, speedThreshold, turnThreshold, options));
    const segments = [];
    labels.forEach((label, frame) => {
        const previous = segments[segments.length - 1];
        if (previous?.label === label) {
            previous.endFrame = frame;
            previous.frameCount += 1;
        } else {
            segments.push({ label, startFrame: frame, endFrame: frame, frameCount: 1 });
        }
    });
    const dt = Number(features?.timestepS) || 1;
    segments.forEach((segment) => {
        segment.startTimeS = segment.startFrame * dt;
        segment.endTimeS = segment.endFrame * dt;
        segment.durationS = segment.frameCount * dt;
    });
    return {
        version: 1,
        scope: 'Rule-based computational behavior segmentation; labels are not biological diagnoses.',
        labels,
        segments,
        thresholds: { speedThreshold, turnThreshold },
        availableLabels: [...LABELS],
    };
}

export function labelFrame(features, frame, speedThreshold = 1e-4, turnThreshold = 0.1, options = {}) {
    const behavior = (features?.metadata?.behaviors ?? []).find((item) => Number(item?.frame ?? item?.startFrame) === frame);
    const explicit = `${behavior?.type ?? ''} ${behavior?.label ?? ''}`.toLowerCase();
    if (/groom/.test(explicit)) return 'Grooming';
    if (/turn/.test(explicit)) return 'Turning';
    if (/walk/.test(explicit)) return 'Walking';
    if (/stand|idle/.test(explicit)) return 'Standing';
    const speed = Number(features?.timeseries?.speed?.[frame]);
    const turnRate = Number(features?.timeseries?.turningRate?.[frame]);
    if (Number.isFinite(turnRate) && turnRate >= turnThreshold) return 'Turning';
    if (Number.isFinite(speed) && speed > speedThreshold) return 'Walking';
    if (Number.isFinite(speed)) return 'Standing';
    return options.defaultLabel && LABELS.includes(options.defaultLabel) ? options.defaultLabel : 'Unknown';
}

export function segmentationSummary(segmentation) {
    const summary = Object.fromEntries(LABELS.map((label) => [label, { count: 0, durationS: 0 }]));
    for (const segment of segmentation?.segments ?? []) {
        summary[segment.label].count += 1;
        summary[segment.label].durationS += segment.durationS;
    }
    return summary;
}
