# 134. Experiment Specification

The canonical matrix is
[`research/campaigns/healthy_baseline/experiment_matrix.csv`](../../research/campaigns/healthy_baseline/experiment_matrix.csv).
It contains exactly 100 planned experiments: `Healthy_001` through
`Healthy_100`, with deterministic seeds 0 through 99.

Each row records the experiment ID, seed, configuration,
`PLANNED` status, expected outputs, validation profile, and publication
targets. The existing `campaign.yaml` supplies campaign metadata and the
execution guard. No row authorizes a simulation or creates a rollout.

Runtime behavior is inherited from the existing Healthy configuration and the
documented V6-V9 orchestration layers. No new runtime profile is invented by
this specification.
