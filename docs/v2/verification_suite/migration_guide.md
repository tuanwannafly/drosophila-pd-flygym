# Migration Guide

Existing callers of `IntegrationWorkflow` require no changes. To add
verification, import `VerificationSuite` and pass the same parsed rollout
object used by the workflow:

```js
import { VerificationSuite } from './verification_suite.js';

const suite = new VerificationSuite();
const report = suite.run(realRollout, {
    sourceName: 'real-rollout.json',
    stress: { iterations: 3 },
});
```

The rollout remains the caller's responsibility. Do not replace it with a
synthetic fixture when producing a scientific verification report.
