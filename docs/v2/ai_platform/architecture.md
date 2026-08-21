# Architecture

The AI-assisted platform is a pure analysis layer for existing computational
behavior data.

## Modules

- `ai_dataset.py`: dataset samples, sequence datasets, indexes, manifests,
  loaders, exporters, versioning, metadata, and checksums.
- `ai_features.py`: trajectory, speed, acceleration, jerk, heading, yaw,
  turning, gait, contact, freezing, exploration, occupancy, curvature,
  tortuosity, episode, and state-statistic features.
- `ai_unsupervised.py`: PCA, UMAP-compatible and t-SNE-compatible deterministic
  embeddings, hierarchical clustering, KMeans, DBSCAN, spectral clustering,
  similarity search, and nearest neighbors.
- `ai_classification.py`: rule-based, distance-based, future-backend-compatible,
  and custom-plugin classification APIs.
- `ai_benchmark.py`: benchmark cases, leaderboards, comparison tables, and
  benchmark reports.
- `ai_report.py`: Markdown, HTML, PDF, JSON, CSV report generation with plots.
- `ai_analytics.py`: dashboard, behavior, cluster, embedding, timeline,
  dataset, and comparison explorer specifications.
- `ai_examples.py`: deterministic synthetic examples for pipeline validation.

## Boundary

The platform does not create scientific evidence, disease labels, biological
validation, or simulation results.
