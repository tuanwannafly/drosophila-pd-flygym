# Regression Review

The pipeline is additive and imports existing `ParkinsonAnalyticsEngine` outputs. It does not modify the FlyGym loader, simulation pipeline, evidence JSON, manuscript, notebooks, or UI modules. The existing web contract test was corrected to tolerate CI repositories with only one commit; it no longer requires `HEAD~1` to exist.

The CI workflow can retain the default shallow checkout because tests no longer require commit history. Local integration skips remain the documented Colab-only FlyGym checks.
