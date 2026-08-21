# Research Campaign Developer Guide

Keep campaign code additive and orchestration-focused.

Do:

- Treat `CampaignConfig` as the source of truth for planned experiments.
- Use stable hashes for experiment IDs, config identity, and manifests.
- Inject rollout execution through `CampaignRunner.run(..., executor=...)`.
- Write artifacts into deterministic campaign directories.
- Preserve provenance for git commit, config hash, dataset hash, artifact hash,
  seed list, software versions, timestamp, and environment.
- Keep biological interpretation outside the campaign engine.

Do not:

- Import FlyGym or MuJoCo inside the campaign engine.
- Modify v1 frozen evidence or manuscript outputs.
- Tune perturbations or introduce new disease claims.
- Treat synthetic CLI outputs as scientific evidence.

Tests should use deterministic synthetic or minimal JSON-like reports unless an
explicit future milestone authorizes simulation execution.
