# Validation Protocol

1. Validate the manifest against `manifest.schema.json`.
2. Validate metadata, source commit, configuration, seed, environment, and
   timing fields.
3. Discover only manifest-declared trajectory files through the existing V7
   adapter.
4. Check file existence, duplicates, byte sizes, SHA-256 values, supported
   formats, and frame counts.
5. Require finite observations and finite derived metrics where the existing
   analysis path reports them.
6. Preserve the deterministic seed and configuration provenance.
7. Stop with `WAITING_DATASET` when the dataset or required payload is absent.
8. Generate reports only after the existing execution gates pass.

These are computational software/data checks. They do not establish biological
validity, disease severity, dopamine depletion, or mechanistic equivalence.
