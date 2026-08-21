# Known Issues

- No raw rollout arrays are stored in this repository's frozen evidence
  reports, so a full runtime verification requires an external real rollout.
- Node.js is not available in the current local shell environment; browser
  or Node execution is required for JavaScript runtime verification.
- A stress point larger than the supplied rollout is reported as
  `insufficient-input`.
- Memory readings are optional and may be `null` when the runtime does not
  expose browser heap telemetry.
