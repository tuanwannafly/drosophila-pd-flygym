# Experiment Workspace Developer Guide

Keep management logic in `web/experiment_workspace.js` and keep DOM concerns in `web/experiment_workspace_panel.js`. Analytics belongs in `web/experiment_analytics.js`; report serialization belongs in `web/experiment_reports.js`. Reuse `FlyGymRolloutLoader`, `computeRolloutStatistics`, and `buildComparisonReport` instead of parsing rollout JSON a second time.

New metrics must declare whether their source channel is available and must return `null` or an empty collection when it is absent. Do not fill missing measurements with fabricated values. Keep report scope language computational and preserve the V1 scientific boundary.
