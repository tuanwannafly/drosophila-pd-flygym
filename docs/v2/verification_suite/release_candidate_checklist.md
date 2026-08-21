# Release Candidate Checklist

## Verification

- [ ] Supply a real FlyGym-compatible rollout.
- [ ] Verify all ordered pipeline stages pass.
- [ ] Verify invalid input rollback passes.
- [ ] Verify two-run deterministic projection passes.
- [ ] Verify all requested stress sizes are measured, including 100,000 frames.
- [ ] Archive timing, memory, cache, input checksum, runtime, and commit metadata.

## Regression

- [ ] Run `python -m compileall -q src scripts tests`.
- [ ] Run `pytest -q -rs -p no:cacheprovider`.
- [ ] Run `git diff --check`.
- [ ] Confirm frozen evidence, manuscript, release artifacts, and notebooks are unchanged.

## Release review

- [ ] Review known issues and limitations.
- [ ] Review migration guidance.
- [ ] Confirm no biological or statistical-significance claims were added.
- [ ] Attach the verification and benchmark reports to the release candidate.
