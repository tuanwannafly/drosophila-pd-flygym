# Regression Report

The experiment workspace is additive to the existing Fly Studio runtime. Existing scene loading, timeline editing, viewport rendering, FlyGym rollout loading, statistics, export, persistence, and playback APIs remain in place. Python repository tests are used for the project regression suite; JavaScript contract tests verify that required browser modules and public symbols remain present.

FlyGym/MuJoCo integration tests remain explicitly skipped locally when those runtime dependencies are unavailable and are verified in the project Colab workflow. Browser interaction requires a manual or hosted Pages check.
