# Reproducibility Checklist

- [ ] Full source commit, branch, and tag are recorded.
- [ ] Approved configuration and configuration hash are recorded.
- [ ] Seeds 0-99 are preserved by experiment ID.
- [ ] Python, FlyGym, MuJoCo, and package versions are recorded.
- [ ] Dataset entries and SHA-256 values are complete.
- [ ] Duration and timestep are recorded from each run.
- [ ] Fresh output paths are used and frozen evidence is untouched.
- [ ] V7 reports `READY` before V6/V8/V9 orchestration.
- [ ] Repeated outputs and manifests are compared deterministically.
- [ ] A `WAITING_DATASET` result is preserved when no real dataset exists.
