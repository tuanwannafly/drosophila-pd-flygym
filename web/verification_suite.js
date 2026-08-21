import { FlyGymRolloutLoader } from './flygym_rollout.js';
import { IntegrationWorkflow } from './integration_workflow.js';

export const REQUIRED_STAGES = Object.freeze([
    'import',
    'validation',
    'normalization',
    'quality-control',
    'feature-extraction',
    'analysis-pipeline',
    'statistical-engine',
    'comparison',
    'parkinson-analytics',
    'visualization',
    'report',
    'export',
    'workspace-persistence',
]);

export const DEFAULT_STRESS_SIZES = Object.freeze([1, 10, 100, 1000, 10000, 100000]);

/**
 * Verification adapter for the existing post-import analysis workflow.
 *
 * This class consumes a caller-supplied rollout. It never creates rollout
 * frames, runs FlyGym, or changes the scientific pipeline. A stress point is
 * marked unavailable when the supplied rollout does not contain enough real
 * frames for that size.
 */
export class VerificationSuite {
    constructor(options = {}) {
        this.workflowOptions = options.workflowOptions ?? options;
        this.workflowFactory = options.workflowFactory ?? (() => new IntegrationWorkflow(this.workflowOptions));
    }

    verifyRollout(rawData, options = {}) {
        const inputRecognized = FlyGymRolloutLoader.canLoad(rawData);
        if (!inputRecognized) {
            return {
                overallPass: false,
                checks: {
                    recognizableRollout: false,
                    requiredStages: false,
                    finiteOutputs: false,
                    exportsPresent: false,
                    persistenceRoundTrip: false,
                },
                stages: [],
                error: 'Input is not a recognizable FlyGym-compatible rollout.',
            };
        }

        const result = this.workflowFactory().importRollout(rawData, options);
        const stages = result.steps ?? [];
        const checks = {
            recognizableRollout: true,
            requiredStages: sameSequence(stages, REQUIRED_STAGES),
            finiteOutputs: !containsNonFinite(result.analysis) && !containsNonFinite(result.statistical),
            exportsPresent: Boolean(result.exported?.json && result.exported?.markdown && result.exported?.html && result.exported?.csv),
            persistenceRoundTrip: result.persistence?.pass === true,
            noRollback: result.rolledBack === false,
            analysisErrors: Array.isArray(result.analysis?.errors) && result.analysis.errors.length === 0,
        };
        return {
            overallPass: Object.values(checks).every(Boolean) && result.overallPass === true,
            checks,
            stages,
            frameCount: result.rollout?.frameCount ?? null,
            format: result.rollout?.source?.format ?? null,
            result: summarizeResult(result),
        };
    }

    verifyRollback() {
        const result = this.workflowFactory().importRollout(null);
        const checks = {
            rejectsInvalidInput: result.rolledBack === true,
            reportsFailure: result.overallPass === false,
            doesNotPersist: result.persistence?.pass === false,
        };
        return { overallPass: Object.values(checks).every(Boolean), checks, stages: result.steps ?? [] };
    }

    verifyDeterminism(rawData, options = {}) {
        const first = this.verifyRollout(rawData, options);
        const second = this.verifyRollout(rawData, options);
        const firstProjection = stableJSON(first.result);
        const secondProjection = stableJSON(second.result);
        const checks = {
            firstRunPasses: first.overallPass,
            secondRunPasses: second.overallPass,
            stableOutputs: firstProjection === secondProjection,
        };
        return { overallPass: Object.values(checks).every(Boolean), checks };
    }

    benchmarkStress(rawData, options = {}) {
        const sizes = options.sizes ?? DEFAULT_STRESS_SIZES;
        const iterations = Math.max(1, Math.floor(options.iterations ?? 3));
        if (!FlyGymRolloutLoader.canLoad(rawData)) {
            return { overallPass: false, availableFrameCount: 0, sizes: [], error: 'A real rollout input is required.' };
        }

        const parsed = FlyGymRolloutLoader.parseData(rawData);
        const rows = sizes.map((size) => {
            if (parsed.frameCount < size) {
                return {
                    requestedFrames: size,
                    status: 'insufficient-input',
                    availableFrames: parsed.frameCount,
                    benchmark: null,
                };
            }
            const input = sliceRollout(rawData, size);
            const benchmark = this.workflowFactory().benchmark(input, { iterations });
            return {
                requestedFrames: size,
                status: 'measured',
                availableFrames: parsed.frameCount,
                benchmark: {
                    iterations: benchmark.iterations,
                    meanMs: benchmark.meanMs,
                    memory: benchmark.memory,
                    cache: benchmark.cache,
                },
            };
        });
        const checks = {
            allRequestedSizesMeasured: rows.every((row) => row.status === 'measured'),
            finiteMeasurements: rows.filter((row) => row.benchmark).every((row) => !containsNonFinite(row.benchmark)),
        };
        return {
            overallPass: Object.values(checks).every(Boolean),
            checks,
            availableFrameCount: parsed.frameCount,
            sizes: rows,
            scientificScope: 'Performance measurements only; no scientific evidence is generated.',
        };
    }

    run(rawData, options = {}) {
        const e2e = this.verifyRollout(rawData, options);
        const rollback = this.verifyRollback();
        const reproducibility = this.verifyDeterminism(rawData, options);
        const stress = this.benchmarkStress(rawData, options.stress ?? {});
        return {
            suiteVersion: 1,
            overallPass: e2e.overallPass && rollback.overallPass && reproducibility.overallPass && stress.overallPass,
            noSimulationExecuted: true,
            syntheticDataUsed: false,
            e2e,
            rollback,
            reproducibility,
            stress,
            scientificBoundary: 'Computational software verification only; no biological validation, diagnosis, disease severity, dopamine equivalence, or mechanistic claim is made.',
        };
    }
}

function sameSequence(actual, expected) {
    return actual.length === expected.length && actual.every((value, index) => value === expected[index]);
}

function summarizeResult(result) {
    return {
        overallPass: result.overallPass,
        rolledBack: result.rolledBack,
        experimentId: result.experiment?.id ?? null,
        statistical: result.statistical,
        comparison: result.comparison,
        parkinson: result.parkinson,
        exported: result.exported,
        persistence: result.persistence,
    };
}

function containsNonFinite(value) {
    if (typeof value === 'number') return !Number.isFinite(value);
    if (Array.isArray(value)) return value.some(containsNonFinite);
    if (value && typeof value === 'object') return Object.values(value).some(containsNonFinite);
    return false;
}

function stableJSON(value) {
    return JSON.stringify(stableValue(value));
}

function stableValue(value, key = '') {
    if (typeof value === 'number' && !Number.isFinite(value)) return String(value);
    if (Array.isArray(value)) return value.map((item) => stableValue(item));
    if (value && typeof value === 'object') {
        return Object.keys(value)
            .filter((name) => !['generatedAt', 'timestamp', 'createdAt', 'updatedAt', 'id'].includes(name))
            .sort()
            .reduce((result, name) => {
                result[name] = stableValue(value[name], name);
                return result;
            }, {});
    }
    return key === 'name' && typeof value === 'string' ? value : value;
}

const SERIES_PATHS = Object.freeze([
    ['frames'],
    ['animation', 'frames'],
    ['trajectory'],
    ['trajectories'],
    ['thorax_positions'],
    ['com_positions'],
    ['body_positions'],
    ['joint_trajectories'],
    ['foot_positions'],
    ['wing_positions'],
    ['head_positions'],
    ['raw_observations', 'thorax_positions'],
    ['raw_observations', 'thorax_orientations'],
    ['observations', 'thorax_positions'],
    ['observations', 'thorax_orientations'],
]);

function sliceRollout(rawData, frameCount) {
    const copy = JSON.parse(JSON.stringify(rawData));
    SERIES_PATHS.forEach((path) => slicePath(copy, path, frameCount));
    return copy;
}

function slicePath(root, path, frameCount) {
    let parent = root;
    for (let index = 0; index < path.length - 1; index += 1) {
        parent = parent?.[path[index]];
        if (!parent) return;
    }
    const key = path[path.length - 1];
    const value = parent?.[key];
    if (Array.isArray(value)) parent[key] = value.slice(0, frameCount);
    else if (value && typeof value === 'object') {
        Object.entries(value).forEach(([name, series]) => {
            if (Array.isArray(series)) value[name] = series.slice(0, frameCount);
        });
    }
}
