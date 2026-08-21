import { buildComparisonReport } from './rollout_comparison.js';

export class ExperimentComparisonModel {
    constructor(experimentWorkspace) {
        this.experimentWorkspace = experimentWorkspace;
    }

    selectedEntries() {
        const ids = new Set(this.experimentWorkspace.comparison.selectedExperimentIds);
        return this.experimentWorkspace.experiments.list().filter((experiment) => ids.has(experiment.id));
    }

    report() {
        const items = this.selectedEntries().flatMap((experiment) => experiment.rollouts.map((item) => ({
            label: experiment.name,
            rollout: item.rollout,
        })));
        return buildComparisonReport(items);
    }

    select(ids) {
        return this.experimentWorkspace.comparison.select(ids);
    }

    synchronize(enabled) {
        return this.experimentWorkspace.comparison.setSynchronized(enabled);
    }

    align(mode, anchor = 0) {
        return this.experimentWorkspace.comparison.setAlignment({ mode, anchor });
    }
}
