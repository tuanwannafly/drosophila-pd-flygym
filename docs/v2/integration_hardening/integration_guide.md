# Integration Guide

```js
import { IntegrationWorkflow } from '../../../web/integration_workflow.js';

const workflow = new IntegrationWorkflow();
const result = workflow.importRollout(rawFlyGymJSON, {
    sourceName: 'rollout.json',
    name: 'Control rollout',
    kind: 'Control',
});
if (!result.overallPass) console.error(result.error, result.analysis?.errors);
```

Use `analyzeBatch` for paired/comparative inputs. Use `benchmark` with a real rollout payload for local performance measurements. This guide does not authorize simulation execution or evidence regeneration.
