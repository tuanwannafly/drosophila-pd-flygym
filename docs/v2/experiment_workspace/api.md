# Experiment Workspace API

```js
import { ExperimentWorkspace } from '../../../web/experiment_workspace.js';
import { ExperimentComparisonModel } from '../../../web/experiment_comparison.js';

const workspace = new ExperimentWorkspace();
const record = workspace.importRollout(normalizedRollout, {
    name: 'control rollout',
    kind: 'Control',
    tags: ['baseline'],
});
workspace.setFilter({ minVelocity: 1 });
const rows = workspace.filteredDataset();
const comparison = new ExperimentComparisonModel(workspace);
workspace.comparison.select([record.id]);
const report = comparison.report();
```

Use `toJSON()` for persistence and `restore(value)` to restore the registry and workspace state. Plugins register an `id`, `type`, and `run(input, context)` function. Supported extension types are analysis, chart, export, and statistics by convention; plugin code remains responsible for its own validation.
