# Manual Validation Checklist

- [ ] Import a valid FlyGym rollout through `IntegrationWorkflow`.
- [ ] Confirm all workflow stages are listed and persistence round-trip passes.
- [ ] Import invalid JSON/structure and confirm structured error plus rollback.
- [ ] Analyze an empty rollout and confirm failure is reported without state loss.
- [ ] Check missing metadata, NaN/Inf values, duplicate frames and broken trajectory warnings.
- [ ] Run a multi-rollout batch and inspect comparison matrices.
- [ ] Run the benchmark and record stage timings/cache hit-miss counts.
- [ ] Confirm no simulation starts and no frozen artifacts change.
