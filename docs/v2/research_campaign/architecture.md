# Research Campaign Architecture

The engine separates planning, execution, data products, and verification.

`CampaignConfig` stores the declared roles, scenarios, stages, interventions,
parameter grid, seeds, replicates, and metadata. `generate_experiment_matrix`
expands this configuration deterministically into `ExperimentPlan` objects.
Each plan receives a stable ID derived from the normalized plan payload.

`CampaignRunner` accepts a `Campaign` and an explicit executor callback. This is
the only boundary where external rollout generation may be plugged in. The
engine itself does not import FlyGym or MuJoCo and does not change controller or
perturbation logic.

Completed outputs can be routed through:

- `CampaignDatasetBuilder` for JSON, CSV, NPZ, and optional columnar datasets.
- `CampaignArtifactManager` for deterministic campaign folders.
- `CampaignFigureFactory` for PNG, SVG, and PDF figures.
- `generate_paper_assets` for `paper_tables`, `paper_figures`,
  `paper_statistics`, and `paper_assets_manifest.json`.
- `CampaignProvenance` and reproducibility helpers for replay and integrity
  verification.

The architecture supports Healthy, Candidate, Progression, Intervention, and
custom scenarios as computational labels only.
