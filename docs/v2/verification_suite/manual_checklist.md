# Manual Validation Checklist

- [ ] Open the web application in a browser with the built modules.
- [ ] Load a real FlyGym-compatible rollout.
- [ ] Run `VerificationSuite.run()` with the same rollout and recorded options.
- [ ] Confirm the end-to-end stage list is complete and ordered.
- [ ] Confirm invalid input reports rollback without replacing workspace state.
- [ ] Confirm the deterministic repeat check passes.
- [ ] Confirm measured stress rows include only sizes available in the rollout.
- [ ] Confirm no console errors and no simulation is started by verification.
- [ ] Record runtime, input checksum, commit, report, and benchmark output.
