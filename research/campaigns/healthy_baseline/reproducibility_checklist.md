# Healthy Baseline Reproducibility Checklist

- [ ] Approved dataset is stored under the contracted Healthy path.
- [ ] Dataset and artifact SHA-256 values are recorded.
- [ ] Full source commit and branch are recorded.
- [ ] Configuration hash and experiment seed are recorded for every run.
- [ ] Python, FlyGym, MuJoCo, and relevant package versions are recorded.
- [ ] Duration and timestep are recorded from the run, not inferred.
- [ ] Fresh execution output path is used; frozen evidence is not overwritten.
- [ ] V7 reports ready and integrity status before V6/V8/V9 orchestration.
- [ ] Repeated outputs are compared using the existing reproducibility checks.
- [ ] Report, figure, table, and bundle manifests are internally consistent.
